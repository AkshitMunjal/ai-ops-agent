import httpx
import streamlit as st

from ui.agent_api_client import (
    dismiss_run,
    get_run_detail,
    get_runs,
    send_decision,
)
from ui.erp_client import (
    approve_reorder,
    cancel_follow_up,
    cancel_reorder,
    get_approved_reorders,
    get_draft_follow_ups,
    get_draft_reorders,
    receive_reorder,
    send_follow_up,
)

review_statuses = ["needs_review", "error", "approval_failed"]


def explain_error(error):
    if isinstance(error, httpx.HTTPStatusError):
        try:
            return error.response.json()["detail"]
        except (ValueError, KeyError):
            return str(error)

    return str(error)


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


def show_draft_reorder(draft_reorder):
    reorder_id = draft_reorder["id"]

    with st.container(border=True):
        st.subheader(f"Reorder {reorder_id}: {draft_reorder['supplier_name']}")

        st.caption("Products to order")
        for line in draft_reorder["lines"]:
            st.write(f"- {line['product_name']} x {line['quantity']}")

        approve_column, cancel_column = st.columns(2)
        clicked_approve = approve_column.button(
            "Approve reorder", key=f"approve-reorder-{reorder_id}", type="primary"
        )
        clicked_cancel = cancel_column.button(
            "Cancel reorder", key=f"cancel-reorder-{reorder_id}"
        )

        if clicked_approve or clicked_cancel:
            try:
                if clicked_approve:
                    approve_reorder(reorder_id)
                else:
                    cancel_reorder(reorder_id)
            except httpx.HTTPError as error:
                st.error(f"The reorder could not be changed: {explain_error(error)}")
            else:
                st.rerun()


def show_approved_reorder(approved_reorder):
    reorder_id = approved_reorder["id"]

    with st.container(border=True):
        st.subheader(f"Reorder {reorder_id}: {approved_reorder['supplier_name']}")

        st.caption("Ordered products")
        for line in approved_reorder["lines"]:
            st.write(f"- {line['product_name']} x {line['quantity']}")

        st.caption("Click when the goods have arrived. The quantities are added to the stock.")
        clicked_received = st.button(
            "Mark received", key=f"receive-reorder-{reorder_id}", type="primary"
        )

        if clicked_received:
            try:
                receive_reorder(reorder_id)
            except httpx.HTTPError as error:
                st.error(f"The reorder could not be changed: {explain_error(error)}")
            else:
                st.rerun()


def show_draft_follow_up(draft_follow_up):
    follow_up_id = draft_follow_up["id"]

    with st.container(border=True):
        st.subheader(f"Reminder {follow_up_id}: invoice {draft_follow_up['invoice_id']}")

        st.caption("To")
        st.write(draft_follow_up["to_email"])

        st.caption("Subject")
        st.write(draft_follow_up["subject"])

        st.caption("Email text")
        st.text(draft_follow_up["body"])

        send_column, cancel_column = st.columns(2)
        clicked_send = send_column.button(
            "Send email", key=f"send-follow-up-{follow_up_id}", type="primary"
        )
        clicked_cancel = cancel_column.button(
            "Cancel draft", key=f"cancel-follow-up-{follow_up_id}"
        )

        if clicked_send or clicked_cancel:
            try:
                if clicked_send:
                    send_follow_up(follow_up_id)
                else:
                    cancel_follow_up(follow_up_id)
            except httpx.HTTPError as error:
                st.error(f"The reminder could not be changed: {explain_error(error)}")
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


st.set_page_config(page_title="Approvals", layout="centered")
st.title("Approvals")

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

try:
    draft_reorders = get_draft_reorders()
    approved_reorders = get_approved_reorders()
    draft_follow_ups = get_draft_follow_ups()
except httpx.HTTPError:
    draft_reorders = None
    approved_reorders = None
    draft_follow_ups = None

st.header("Orders waiting for approval")
if not waiting_runs:
    st.success("Nothing is waiting. All emails are handled.")
for run in waiting_runs:
    show_waiting_run(run)

st.divider()

st.header("Stock reorders waiting for approval")
if draft_reorders is None:
    st.error("Cannot reach the ERP. Is it running on port 8000?")
elif not draft_reorders:
    st.success("No reorders are waiting.")
else:
    for draft_reorder in draft_reorders:
        show_draft_reorder(draft_reorder)

st.divider()

st.header("Approved reorders, goods not received yet")
if approved_reorders is None:
    st.error("Cannot reach the ERP. Is it running on port 8000?")
elif not approved_reorders:
    st.success("No goods are on the way.")
else:
    for approved_reorder in approved_reorders:
        show_approved_reorder(approved_reorder)

st.divider()

st.header("Payment reminders waiting to be sent")
if draft_follow_ups is None:
    st.error("Cannot reach the ERP. Is it running on port 8000?")
elif not draft_follow_ups:
    st.success("No reminders are waiting.")
else:
    for draft_follow_up in draft_follow_ups:
        show_draft_follow_up(draft_follow_up)

st.divider()

st.header("Needs review")
if not review_runs:
    st.success("No problems to review.")
for run in review_runs:
    show_review_run(run)