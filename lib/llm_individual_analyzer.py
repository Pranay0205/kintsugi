
from time import time
from typing import Hashable
from dotenv import load_dotenv
from google import genai

from utils.constants import BATCH_SIZE, GEMINI_API_KEY


load_dotenv()

client = genai.Client(api_key=GEMINI_API_KEY)


def analyze_individual_submissions(submissions: list[dict[Hashable, str]]) -> str | None:
    prompt = """You are an expert code reviewer. Analyze the following code submissions and provide general gaps of knowledge that the authors should focus on to improve their coding skills. Provide a concise list of areas for improvement without going into specific details about each submission."""

    formatted_submissions = __format_submissions_for_batch(
        prompt, submissions[:BATCH_SIZE])

    inline_batch_job = client.batches.create(
        model="models/gemini-2.5-flash",
        src=formatted_submissions,
        config={
            'display_name': "submission_analysis_batch",
        },
    )

    print(f"Created batch job: {inline_batch_job.name}")

    return inline_batch_job.name


def get_job_status(batch_job_name: str):
    batch_job = client.batches.get(name=batch_job_name)

    completed_states = set([
        'JOB_STATE_SUCCEEDED',
        'JOB_STATE_FAILED',
        'JOB_STATE_CANCELLED',
        'JOB_STATE_EXPIRED',
    ])

    print(f"Polling batch job: {batch_job.name}")

    while batch_job.state is not None and batch_job.state.name not in completed_states:
        print(
            f"Current state: {batch_job.state.name} - waiting 30 seconds before next check...")
        time.sleep(30)
        batch_job = client.batches.get(name=batch_job_name)

    if batch_job.state is not None and batch_job.state.name == 'JOB_STATE_FAILED':
        print(f"Error: {batch_job.error}")

    if batch_job.state is not None:
        print(f"Job finished with state: {batch_job.state.name}")


def get_batch_results(batch_job_name: str):

    batch_job = client.batches.get(name=batch_job_name)

    if batch_job.state is not None and batch_job.state.name == 'JOB_STATE_SUCCEEDED':

        inlined_responses = batch_job.dest and getattr(
            batch_job.dest, 'inlined_responses', None)

        if inlined_responses:
            print("Batch Results:")
            for i, inline_response in enumerate(inlined_responses):
                print(f"Result for submission {i + 1}:")
                response = getattr(inline_response, 'response', None)
                if response:
                    try:
                        text = getattr(response, 'text', None)
                        if text:
                            print(text)
                        else:
                            print("No text response available.")
                    except AttributeError:
                        print("No text response available.", response)
                    print("\n")
                else:
                    print("No response available for this submission.")
        else:
            print("No inlined responses found in the batch job destination.")
    else:
        print(
            f"Batch job not succeeded. Current state: {batch_job.state.name if batch_job.state else 'Unknown'}")


def __format_submissions_for_batch(prompt: str, submissions: list[dict[Hashable, str]]) -> list[dict]:
    batch = []
    for submission in submissions:
        batch.append({
            'contents': [{
                'parts': [{'text': f"{prompt}\n\n{submission['CodeContent']}"}],
                'role': 'user'
            }]
        })

    return batch
