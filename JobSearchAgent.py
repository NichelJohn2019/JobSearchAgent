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

# GraphQL client function to send requests
def graphql_query(query: str, variables: dict = None, endpoint: str = "https://i-05558d22b86fdf971.workdaysuv.com/graphql/v1/super"):
    headers = {
        "accept": "application/json",
        "authorization": 
        "ID eyJraWQiOiJFc2IiLCJhbGciOiJSUzUxMiJ9.eyJpc3MiOiJPTVMiLCJhdXRoX3RpbWUiOjE3NDM1MzM0ODMsImNoYW5uZWwiOiJXZWIgU2VydmljZXMiLCJhdXRoX3R5cGUiOiJVbml2ZXJzYWxQYXNzd29yZCIsInN5c19hY2N0X3R5cCI6Ik4iLCJpbnRTdWIiOiJ3ZC1kZXYiLCJ3aWQiOiIzNGNkNWZjYTE1ZGQ0MWQ2OThiMDY2NzAxMWU0YzliZCIsImVuY3J5cHRlZFNlc3Npb25JZCI6Ii9LVGxuWXhSa3Y4ZXRScG5DZVVSZ2VmV0RWTlI2REF1V25DTkZpRXpiL3lNc0ZQbVhGUGRpQWROc2hMN3pzTE06NktoTkRBdVdIZkxhNXJEUW96UkVOQVx1MDAzZFx1MDAzZDoxIiwic2Vzc2lvbl9pZF90eXBlIjoiT01TIiwidG9rZW5UeXBlIjoiSWRlbnRpdHkiLCJzdWIiOiJTdXBlclVzZXIiLCJhdWQiOiJ3ZCIsImV4cCI6MTc0MzYxNDY3NSwiaWF0IjoxNzQzNjEzNzc1LCJqdGkiOiJpamk1aDNkNDRiOTczcmc4OHI1MTM3YXNnYzkxMjBjdzJkeHp2enVmYWhuM2o4enYyNWYza2IwNnJkaWN5MnFnOTVyMXI3dzhyMWR5d3VqbGtrazFobHdkeG95Z3lmdGNqZTdnejFzYnVtdHV4cXF4ODVldDFwOTRoNnhnZHN3MWVkYXBwb2EydXl6ZGJ6NTloa3A3dzlwNmY0djRwbzZlcHZkejcxMWw3YWt4ZTl4Nm13cTNjdGIwcWozZzJiOG9mb3gzaGUxN3VjNzRkMXhiY3A5bnkyMWJobmltNWNhc2NwN2R4MGdxOTJsaGg2cmFzOXAydmJnbXBibXBmNWI5dDkybHVuNzk3cDJic2xwY3RzcTU1Mnk5NWo2a3lmcXhldzlqb256YmFoZnB1OXgzbGh0OHR0MjdmdDJ0NWtvYWozeHNhZDRheHJybXNmejk4c293YzB5eGJnZmtxNGVhb3I5eHp3cTJtYW9zeWV2N2kybnphcDdpZmE3aGg3eTFubTc0a2d3aGk4dGgiLCJ0ZW5hbnQiOiJzdXBlciJ9.Xf2PS0BoFjiGJHFq9Y7W8D6V_WHc2pERvZmCzoF4-n399f5KP1UGoO3SdGOn--1JSkTUrs3KzemWPv94EynmgceuTekJxhc-0NAYk9qvpo95VT_pLVoJH6-246V3bZdWeS4fBSIdXCqzPEJo7xwqc65kGDNziWvHGNJg74S49-QfTqvFHybOHG9eO6zXnbObRhxzLduw9bic91I7t6cLV6CmPJMYiQa9M-e4cbAmc51OdQw2xAHF46pr8qWof9dDIlmdiH5Iqt1vsBYR8CpJqk1hfHXm9lKn6Y1CRSgPyO12jg6quirLSgqJNJK8MXW8pO9Te8uH8Kkgl-pecWC7Yw",  # Left blank for manual input
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
        # print(f"Raw API Response: {result}")
        return result
    except requests.exceptions.RequestException as e:
        error_msg = {"error": f"{str(e)} - Response: {e.response.text if e.response else 'No response'}"}
        print(f"API Error: {error_msg}")
        return error_msg

# Node to ask for user's name
def ask_for_name(state: AgentState) -> AgentState:
    if state["step"] == "start":
        greeting = (
            "Hi there! I'm your job search assistant. "
            "To get started, could you please tell me your name?"
        )
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
        response = (
            f"Nice to meet you, {name}! Now, what job position would you like me to search for? "
            "For example, you could say 'Software Engineer' or 'Chief Financial Officer'."
        )
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
        response = (
            f"Got it, {state['user_name']}! I'll look up some info about '{job}' positions. "
            "Hang on while I check the job database..."
        )
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

# Node to format and explain response
def format_response(state: AgentState) -> AgentState:
    if state["step"] != "formatting":
        return state
    
    response = state["response"]
    print(f"Formatting response: {response}")
    if "error" in response or (response.get("data") and response["data"].get("jobProfile") is None):
        message = (
            f"Sorry, {state['user_name']}, I ran into an issue: {response.get('error', response.get('errors', ['Unknown error'])[0])}. "
            "Maybe try a different job title or check your API credentials?"
        )
    else:
        data = response.get("data", {}).get("jobProfile", {}).get("data", [])
        total = response.get("data", {}).get("jobProfile", {}).get("total", 0)
        print(f"Extracted data: {data}")
        if not data:
            message = (
                f"Hmm, {state['user_name']}, I couldn’t find any '{state['job_query']}' positions. "
                "Would you like me to search for something else?"
            )
        else:
            # Lenient filtering: partial match, case-insensitive
            filtered_data = [job for job in data if state["job_query"].lower() in job.get("jobProfileName", "").lower()]
            print(f"Filtered data for '{state['job_query']}': {filtered_data}")
            if not filtered_data:
                message = (
                    f"Hmm, {state['user_name']}, I couldn’t find any positions matching '{state['job_query']}'. "
                    "Would you like me to search for something else?"
                )
            else:
                message = (
                    f"Good news, {state['user_name']}! Here’s what I found for '{state['job_query']}':\n"
                )
                for job in filtered_data:
                    message += (
                        f"- {job.get('jobProfileName', 'Untitled Job')}\n"
                        f"  ID: {job.get('jobProfileId', 'Not specified')}\n"
                        f"  Description: {job.get('jobDescription', 'No description available') or 'None'}\n"
                    )
                message += f"Total matching results: {len(filtered_data)} (out of {total} total profiles)\n"
                message += "Would you like me to search for another position?"

    return {
        "messages": state["messages"] + [AIMessage(content=message)],
        "user_name": state["user_name"],
        "job_query": state["job_query"],
        "response": state["response"],
        "step": "done"
    }

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("ask_for_name", ask_for_name)
workflow.add_node("process_name", process_name)
workflow.add_node("process_job_query", process_job_query)
workflow.add_node("execute_query", execute_query)
workflow.add_node("format_response", format_response)

# Define edges
workflow.add_edge("ask_for_name", "process_name")
workflow.add_edge("process_name", "process_job_query")
workflow.add_edge("process_job_query", "execute_query")
workflow.add_edge("execute_query", "format_response")
workflow.add_edge("format_response", END)

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
        
        if state["step"] in ["waiting_for_name", "waiting_for_job"]:
            user_input = input("You: ")
            state["messages"].append(HumanMessage(content=user_input))
    
    # print("\nFull conversation:")
    # for message in state["messages"]:
    #     if isinstance(message, HumanMessage) and message.content != "start":
    #         print(f"You: {message.content}")
    #     elif isinstance(message, AIMessage):
    #         print(f"Agent: {message.content}")

if __name__ == "__main__":
    run_agent()