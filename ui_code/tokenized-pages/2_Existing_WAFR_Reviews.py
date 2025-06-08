import streamlit as st
from streamlit_lottie import st_lottie
import pandas as pd
import boto3
import json
from boto3.dynamodb.types import TypeDeserializer
import os

# Set AWS credentials securely
os.environ['AWS_ACCESS_KEY_ID'] = st.secrets["AWS_ACCESS_KEY_ID"]
os.environ['AWS_SECRET_ACCESS_KEY'] = st.secrets["AWS_SECRET_ACCESS_KEY"]
os.environ['AWS_REGION'] = st.secrets["AWS_REGION"]

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning('You are not logged in. Please log in to access this page.')
    st.switch_page("pages/1_Login.py")

st.set_page_config(page_title="WAFR Analysis Grid", layout="wide")

def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_animation = load_lottie_file("ui_code/assets/Animation - 1749331773347.json")
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st_lottie(lottie_animation, height=250, key="welcome")
st.markdown("</div>", unsafe_allow_html=True)

def logout():
    st.session_state['authenticated'] = False
    st.session_state.pop('username', None)
    st.rerun()

if st.sidebar.button('Logout'):
    logout()

# AWS clients
client = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
dynamodb = boto3.client("dynamodb", region_name=os.environ["AWS_REGION"])

# Use inference profile ARN as modelId
model_id = st.secrets["INFERENCE_PROFILE_ARN"]

def load_data():
    try:
        response = dynamodb.scan(TableName=st.secrets["WAFR_ACCELERATOR_RUNS_DD_TABLE_NAME"])
        items = response['Items']
        while 'LastEvaluatedKey' in response:
            response = dynamodb.scan(
                TableName=st.secrets["WAFR_ACCELERATOR_RUNS_DD_TABLE_NAME"],
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])

        if not items:
            st.warning("There are no existing WAFR review records")
            return pd.DataFrame()

        deserializer = TypeDeserializer()
        data = [{k: deserializer.deserialize(v) for k, v in item.items()} for item in items]
        df = pd.DataFrame(data)

        column_mapping = {
            'analysis_id': 'Analysis Id',
            'analysis_title': 'Workload Name',
            'workload_desc': 'Workload Description',
            'analysis_review_type': 'Analysis Type',
            'selected_lens': 'WAFR Lens',
            'creation_date': 'Creation Date',
            'review_status': 'Status',
            'analysis_submitter': 'Created By',
            'review_owner': 'Review Owner',
            'extracted_document': 'Document',
            'architecture_summary': 'Solution Summary'
        }

        df.rename(columns=column_mapping, inplace=True)

        for col in column_mapping.values():
            if col not in df.columns:
                df[col] = ''

        if 'pillars' in df.columns:
            df['pillars'] = df['pillars'].apply(
                lambda p: p if isinstance(p, list) else [])
        else:
            df['pillars'] = [[] for _ in range(len(df))]

        if 'selected_wafr_pillars' not in df.columns:
            df['selected_wafr_pillars'] = ''

        return df[[
            'Analysis Id', 'Workload Name', 'Workload Description', 'Analysis Type',
            'WAFR Lens', 'Creation Date', 'Status', 'Created By', 'Review Owner',
            'Solution Summary', 'pillars', 'selected_wafr_pillars', 'Document'
        ]]
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

def display_summary(analysis):
    st.subheader("Summary")
    selected_pillars = ', '.join(analysis['selected_wafr_pillars']) if isinstance(analysis['selected_wafr_pillars'], list) else str(analysis['selected_wafr_pillars'])
    summary_data = {
        "Field": ["Analysis Id", "Workload Name", "Workload Description", "Analysis Type", "Status", "WAFR Lens", "Creation Date", "Created By", "Review Owner", "Selected WAFR Pillars"],
        "Value": [
            analysis['Analysis Id'],
            analysis['Workload Name'],
            analysis['Workload Description'],
            analysis['Analysis Type'],
            analysis['Status'],
            analysis['WAFR Lens'],
            analysis['Creation Date'],
            analysis['Created By'],
            analysis['Review Owner'],
            selected_pillars
        ]
    }
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

def parse_stream(stream):
    for event in stream:
        chunk = event.get('chunk')
        if chunk:
            message = json.loads(chunk.get("bytes").decode())
            if message['type'] == "content_block_delta":
                yield message['delta']['text']
            elif message['type'] == "message_stop":
                return "\n"

def main():
    st.title("WAFR Analysis")
    st.subheader("WAFR Analysis Runs", divider="rainbow")

    df = load_data()
    if df.empty:
        return

    st.dataframe(df[['Analysis Id', 'Workload Name', 'Analysis Type', 'WAFR Lens', 'Creation Date', 'Status', 'Created By']], use_container_width=True)

    selected_name = st.selectbox("Select an analysis to view details:", df['Workload Name'].tolist())
    if not selected_name:
        return

    record = df[df['Workload Name'] == selected_name].iloc[0]
    tab_titles = ["Summary", "Solution Summary"] + [p['pillar_name'] for p in record['pillars']]
    tabs = st.tabs(tab_titles)

    with tabs[0]:
        display_summary(record)
    with tabs[1]:
        st.subheader("Solution Summary")
        st.write(record['Solution Summary'])

    for i, pillar in enumerate(record['pillars'], start=2):
        with tabs[i]:
            st.subheader(f"Review findings & recommendations for pillar: {pillar['pillar_name']}")
            st.write(pillar.get('llm_response', 'No data'))

    st.subheader("WAFR Chat", divider="rainbow")
    chat_areas = ["Summary", "Solution Summary", "Document"] + [p['pillar_name'] for p in record['pillars']]
    selected_area = st.selectbox("Select area for chat:", chat_areas)
    prompt = st.text_input("Ask a question:")

    if prompt:
        if selected_area == "Summary":
            context = f"""
            WAFR Analysis Summary:
            Workload Name: {record['Workload Name']}
            Description: {record['Workload Description']}
            Status: {record['Status']}
            Lens: {record['WAFR Lens']}
            Created By: {record['Created By']}
            Review Owner: {record['Review Owner']}
            Date: {record['Creation Date']}
            Pillars: {record['selected_wafr_pillars']}
            Solution Summary: {record['Solution Summary']}
            """
        elif selected_area == "Solution Summary":
            context = f"Solution Summary:\n{record['Solution Summary']}"
        elif selected_area == "Document":
            context = f"Document:\n{record['Document']}"
        else:
            pillar = next((p for p in record['pillars'] if p['pillar_name'] == selected_area), None)
            context = pillar.get('llm_response', 'No data') if pillar else 'No data'

        full_prompt = f"{context.strip()}\n\nUser Question: {prompt}"

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": full_prompt[:4000]}]
            }]
        })

        try:
            response = client.invoke_model(
                modelId=model_id,  # Use inference profile ARN directly
                contentType="application/json",
                accept="application/json",
                body=body.encode("utf-8")
            )

            response_body = json.loads(response["body"].read().decode("utf-8"))
            answer = response_body.get("content", [])[0].get("text", "").strip()

            st.subheader("Response")
            st.write(answer)

        except Exception as e:
            st.error("Model invocation failed.")
            st.exception(e)

if __name__ == "__main__":
    main()
