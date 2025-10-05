import streamlit as st
from datetime import date
from db import insert_efficiency, list_efficiency, update_efficiency, delete_efficiency

st.title("6) Efficiency (Physical Condition)")

tab_add, tab_edit = st.tabs(["Add", "Edit / Delete"])

# -------- Add Tab --------
with tab_add:
    with st.form("eff_add"):
        col1, col2 = st.columns(2)
        with col1:
            s = st.date_input("Start Date", value=date.today(), format="YYYY-MM-DD")
            e = st.date_input("End Date", value=date.today(), format="YYYY-MM-DD")
        eff = st.slider("Efficiency (%)", min_value=0, max_value=100, value=80, step=1)

        rep = st.selectbox("Repeat", ["One-time only", "Repeat"])

        # Show cycle selection only when "Repeat" is chosen
        interval_edit = None
        interval_placeholder = "— Select —"
        if rep == "Repeat":
            options = [interval_placeholder] + list(range(1, 31))
            chosen = st.selectbox("Interval (days)", options, index=0, key="interval_days_select")
            if chosen != interval_placeholder:
                interval_edit = int(chosen)

        # Validation
        can_submit = True
        msg = None
        if e < s:
            can_submit = False
            msg = "The end date must be on or after the start date."
        if rep == "Repeat" and interval_edit is None:
            can_submit = False
            msg = "Please select an interval (days)."

        submitted = st.form_submit_button("Add", disabled=not can_submit)

        if submitted:
            insert_efficiency(
                s.isoformat(),
                e.isoformat(),
                eff / 100.0,
                1 if rep == "Repeat" else 0,
                interval_edit if rep == "Repeat" else None,
            )
            st.success("Added successfully.")
            st.rerun()

        if msg and not submitted:
            st.info(msg)

# -------- Edit/Delete Tab --------
with tab_edit:
    st.subheader("Registered Entries")
    rows = list_efficiency()

    if not rows:
        st.info("No entries found.")
    else:
        for r in rows:
            try:
                s_default = date.fromisoformat(r["start_date"])
                e_default = date.fromisoformat(r["end_date"])
            except Exception:
                s_default = date.today()
                e_default = date.today()

            eff_pct = int(round((r.get("efficiency") or 0.0) * 100))
            rep_default = "Repeat" if (r.get("repeat") or 0) == 1 else "One-time only"
            interval_default = r.get("interval_days")

            header = f"ID {r['id']} | {r['start_date']} → {r['end_date']} | {eff_pct}% | {'Repeat' if rep_default == 'Repeat' else 'Single'}"
            with st.expander(header, expanded=False):
                with st.form(f"eff_edit_{r['id']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        s_edit = st.date_input("Start Date", value=s_default, format="YYYY-MM-DD", key=f"s_{r['id']}")
                        e_edit = st.date_input("End Date", value=e_default, format="YYYY-MM-DD", key=f"e_{r['id']}")
                    eff_edit = st.slider("Efficiency (%)", min_value=0, max_value=100, value=eff_pct, step=1, key=f"eff_{r['id']}")
                    rep_edit = st.selectbox("Repeat", ["One-time only", "Repeat"],
                                            index=(0 if rep_default == "One-time only" else 1), key=f"rep_{r['id']}")

                    interval_edit_row = None
                    if rep_edit == "Repeat":
                        options_row = [interval_placeholder] + list(range(1, 31))
                        if isinstance(interval_default, int) and 1 <= interval_default <= 30:
                            init_idx = options_row.index(interval_default)
                        else:
                            init_idx = 0
                        chosen_row = st.selectbox("Interval (days)", options_row, index=init_idx, key=f"int_{r['id']}")
                        if chosen_row != interval_placeholder:
                            interval_edit_row = int(chosen_row)

                    colu = st.columns(3)
                    with colu[0]:
                        save = st.form_submit_button("Save",
                            disabled=(e_edit < s_edit) or (rep_edit == "Repeat" and interval_edit_row is None))
                    with colu[1]:
                        delete = st.form_submit_button("Delete", type="primary")
                    with colu[2]:
                        cancel = st.form_submit_button("Cancel")

                if save:
                    updated = update_efficiency(
                        r["id"],
                        s_edit.isoformat(),
                        e_edit.isoformat(),
                        eff_edit / 100.0,
                        1 if rep_edit == "Repeat" else 0,
                        interval_edit_row if rep_edit == "Repeat" else None,
                    )
                    if updated == 1:
                        st.success("Updated successfully.")
                        st.rerun()
                    else:
                        st.warning("No record found to update.")

                if delete:
                    removed = delete_efficiency(r["id"])
                    if removed == 1:
                        st.success("Deleted successfully.")
                        st.rerun()
                    else:
                        st.warning("No record found to delete.")
