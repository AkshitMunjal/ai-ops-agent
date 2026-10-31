import httpx
import streamlit as st

from ui.agent_api_client import (
    dismiss_run,
    get_run_detail,
    get_runs,
    send_decision,
)

review_statuses = ["needs_review", "error", "approval_failed"]


def show_waiting_run(run):
    run_id = run["id"]
    run_detail = get_run_detail(run_id)
    understood = run_detail["understood"]

    with st.container(border=True):
        st.subheader(f"Run {run_id}, draft order {run['draft_order_id']}")

        st.caption("Original email")
        st.text(run["email_text"])

        st.caption("What the agent understood")
        if understood is None:
            st.warning("The details of this run could not be loaded.")
        else:
            st.write("Customer: " + understood["customer_name"])
            for line in understood["lines"]:
                st.write(f"- {line['product_name']} x {line['quantity']}")

        approve_column, reject_column = st.columns(2)
        clicked_approve = approve_column.button(
            "Approve", key=f"approve-{run_id}", type="primary"
        )
        clicked_reject = reject_column.button("Reject", key=f"reject-{run_id}")

        decision = None
        if clicked_approve:
            decision = "approve"
        if clicked_reject:
            decision = "reject"

        if decision is not None:
            try:
                send_decision(run_id, decision)
            except httpx.HTTPError as error:
                st.error(f"The decision could not be saved: {error}")
            else:
                st.rerun()


def show_review_run(run):
    run_id = run["id"]

    with st.container(border=True):
        st.subheader(f"Run {run_id}: {run['status']}")

        st.caption("Original email")
        st.text(run["email_text"])

        st.caption("What went wrong")
        if run["problems"]:
            st.error(run["problems"])
        else:
            st.error("No reason was saved for this run.")

        clicked_dismiss = st.button("Dismiss", key=f"dismiss-{run_id}")
        if clicked_dismiss:
            try:
                dismiss_run(run_id)
            except httpx.HTTPError as error:
                st.error(f"The run could not be dismissed: {error}")
            else:
                st.rerun()


st.set_page_config(page_title="Order approvals", layout="centered")
st.title("Order approvals")

if st.button("Refresh"):
    st.rerun()

try:
    waiting_runs = get_runs("waiting_for_approval")
    review_runs = []
    for status in review_statuses:
        review_runs.extend(get_runs(status))
except httpx.HTTPError:
    st.error("Cannot reach the agent service. Is it running on port 8001?")
    st.stop()

st.header("Waiting for approval")
if not waiting_runs:
    st.success("Nothing is waiting. All emails are handled.")
for run in waiting_runs:
    show_waiting_run(run)

st.divider()

st.header("Needs review")
if not review_runs:
    st.success("No problems to review.")
for run in review_runs:
    show_review_run(run)