from typing import TypedDict, Annotated, Sequence
import requests
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[Sequence[HumanMessage | AIMessage], "The messages in the conversation"]
    user_name: str
    job_query: str
    response: dict
    step: str

# GraphQL client function with blank token
def graphql_query(query: str, variables: dict = None, endpoint: str = "https://i-05558d22b86fdf971.workdaysuv.com/graphql/v1/super"):
    headers = {
        "accept": "application/json",
        "authorization": "",  # Left blank for manual input
        "content-type": "application/json"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    try:
        print(f"Sending request with payload: {payload}")
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        print(f"Raw API Response: {result}")
        return result
    except requests.exceptions.RequestException as e:
        error_msg = {"error": f"{str(e)} - Response: {e.response.text if e.response else 'No response'}"}
        print(f"API Error: {error_msg}")
        return error_msg

# Node to ask for user's name
def ask_for_name(state: AgentState) -> AgentState:
    if state["step"] == "start":
        greeting = "Hi! I’m here to find you a job. What’s your name?"
        return {
            "messages": state["messages"] + [AIMessage(content=greeting)],
            "user_name": "",
            "job_query": "",
            "response": {},
            "step": "waiting_for_name"
        }
    return state

# Node to process name and ask for job query
def process_name(state: AgentState) -> AgentState:
    if state["step"] != "waiting_for_name":
        return state
    
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        name = last_message.content.strip()
        response = f"Hey {name}, what job are we looking for?"
        return {
            "messages": state["messages"] + [AIMessage(content=response)],
            "user_name": name,
            "job_query": "",
            "response": {},
            "step": "waiting_for_job"
        }
    return state

# Node to process job query
def process_job_query(state: AgentState) -> AgentState:
    if state["step"] != "waiting_for_job":
        return state
    
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        job = last_message.content.strip()
        response = f"Got it, {state['user_name']}. Checking for '{job}' now..."
        return {
            "messages": state["messages"] + [AIMessage(content=response)],
            "user_name": state["user_name"],
            "job_query": job,
            "response": {},
            "step": "querying"
        }
    return state

# Node to execute GraphQL query
def execute_query(state: AgentState) -> AgentState:
    if state["step"] != "querying":
        return state
    
    graphql_query_str = """
    query jobProfile($jobProfile_dataSource: JobProfile_DataSources!) {
      jobProfile(dataSource: $jobProfile_dataSource) {
        data {
          jobProfileId
          jobProfileName
          jobDescription
        }
        total
      }
    }
    """
    variables = {
        "jobProfile_dataSource": {
            "allActiveJobProfiles": {
                "filter": {
                    "defaultFilter": {}
                }
            }
        }
    }
    result = graphql_query(graphql_query_str, variables)
    
    return {
        "messages": state["messages"],
        "user_name": state["user_name"],
        "job_query": state["job_query"],
        "response": result,
        "step": "formatting"
    }

# Node to format response
def format_response(state: AgentState) -> AgentState:
    if state["step"] != "formatting":
        return state
    
    response = state["response"]
    print(f"Formatting response: {response}")
    if "error" in response or (response.get("data") and response["data"].get("jobProfile") is None):
        error_detail = response.get('error', response.get('errors', ['Oops, something broke'])[0])
        message = f"Sorry, {state['user_name']}, there’s an issue: {error_detail}. Try again?"
        next_step = "waiting_for_job"
    else:
        data = response.get("data", {}).get("jobProfile", {}).get("data", [])
        total = response.get("data", {}).get("jobProfile", {}).get("total", 0)
        print(f"Extracted data: {data}")
        if not data:
            message = f"No jobs found for '{state['job_query']}', {state['user_name']}. Another search? Yes or no?"
            next_step = "waiting_for_continue"
        else:
            filtered_data = [job for job in data if state["job_query"].lower() in job.get("jobProfileName", "").lower()]
            print(f"Filtered data for '{state['job_query']}': {filtered_data}")
            if not filtered_data:
                message = f"No match for '{state['job_query']}', {state['user_name']}. Another go? Yes or no?"
                next_step = "waiting_for_continue"
            else:
                message = f"Here’s what I found for '{state['job_query']}', {state['user_name']}:\n"
                for job in filtered_data:
                    message += (
                        f"- {job.get('jobProfileName', 'No Name')} (ID: {job.get('jobProfileId', '???')})\n"
                        f"  Info: {job.get('jobDescription', 'None') or 'None'}\n"
                    )
                message += f"Found {len(filtered_data)} of {total} jobs. Search again? Yes or no?"
                next_step = "waiting_for_continue"

    return {
        "messages": state["messages"] + [AIMessage(content=message)],
        "user_name": state["user_name"],
        "job_query": "",
        "response": {},
        "step": next_step
    }

# Node to handle the "yes/no" response
def handle_continue(state: AgentState) -> AgentState:
    if state["step"] != "waiting_for_continue":
        return state
    
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage):
        response = last_message.content.strip().lower()
        if response in ["yes", "y", "yep", "sure"]:
            message = f"Okay, {state['user_name']}, what’s next?"
            return {
                "messages": state["messages"] + [AIMessage(content=message)],
                "user_name": state["user_name"],
                "job_query": "",
                "response": {},
                "step": "waiting_for_job"
            }
        elif response in ["no", "n", "nope"]:
            message = f"Alright, {state['user_name']}, we’re done here. Catch you later!"
            return {
                "messages": state["messages"] + [AIMessage(content=message)],
                "user_name": state["user_name"],
                "job_query": "",
                "response": {},
                "step": "done"
            }
        else:
            message = f"Sorry, {state['user_name']}, just say 'yes' or 'no'."
            return {
                "messages": state["messages"] + [AIMessage(content=message)],
                "user_name": state["user_name"],
                "job_query": "",
                "response": {},
                "step": "waiting_for_continue"
            }
    return state

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("ask_for_name", ask_for_name)
workflow.add_node("process_name", process_name)
workflow.add_node("process_job_query", process_job_query)
workflow.add_node("execute_query", execute_query)
workflow.add_node("format_response", format_response)
workflow.add_node("handle_continue", handle_continue)

# Define edges
workflow.add_edge("ask_for_name", "process_name")
workflow.add_edge("process_name", "process_job_query")
workflow.add_edge("process_job_query", "execute_query")
workflow.add_edge("execute_query", "format_response")
workflow.add_edge("format_response", "handle_continue")
workflow.add_edge("handle_continue", "process_job_query", condition=lambda state: state["step"] == "waiting_for_job")
workflow.add_edge("handle_continue", END, condition=lambda state: state["step"] == "done")

# Set entry point
workflow.set_entry_point("ask_for_name")

# Compile the graph
graph = workflow.compile()

# Function to run the agent interactively
def run_agent():
    state = {
        "messages": [HumanMessage(content="start")],
        "user_name": "",
        "job_query": "",
        "response": {},
        "step": "start"
    }
    
    print("Starting conversation...\n")
    
    while state["step"] != "done":
        state = graph.invoke(state)
        latest_message = state["messages"][-1]
        if isinstance(latest_message, AIMessage):
            print(f"Agent: {latest_message.content}")
        
        if state["step"] in ["waiting_for_name", "waiting_for_job", "waiting_for_continue"]:
            user_input = input("You: ")
            state["messages"].append(HumanMessage(content=user_input))
    
    print("\nFull conversation:")
    for message in state["messages"]:
        if isinstance(message, HumanMessage) and message.content != "start":
            print(f"You: {message.content}")
        elif isinstance(message, AIMessage):
            print(f"Agent: {latest_message.content}")

if __name__ == "__main__":
    run_agent()