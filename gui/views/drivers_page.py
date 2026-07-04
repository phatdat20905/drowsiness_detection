# views/drivers_page.py  –  Quản lý tài xế (Admin)
import streamlit as st
import pandas as pd

from components.styles import inject_css, section_header, page_header, badge
from database.db import (
    get_all_users, create_user, update_user,
    delete_user, toggle_user_active, get_user,
)


def render():
    inject_css()
    page_header("👥 Quản lý tài xế", "Thêm, sửa, xóa và tìm kiếm tài xế")

    tabs = st.tabs(["📋  Danh sách", "➕  Thêm mới"])

    # ════════════════════════════════════════════════════════
    #  Tab 1 – Danh sách
    # ════════════════════════════════════════════════════════
    with tabs[0]:
        # Search + filter bar
        sc1, sc2 = st.columns([3, 1])
        with sc1:
            search = st.text_input("🔍", placeholder="Tìm theo tên, username, email...",
                                   label_visibility="collapsed")
        with sc2:
            show_inactive = st.checkbox("Hiện tài khoản vô hiệu")

        users = get_all_users(role="driver", search=search or None)
        if not show_inactive:
            users = [u for u in users if u["is_active"]]

        if not users:
            st.info("Không tìm thấy tài xế nào.")
        else:
            # Header row
            h0, h1, h2, h3, h4, h5 = st.columns([2, 2.5, 2, 1.5, 1.5, 2])
            for col, label in zip([h0,h1,h2,h3,h4,h5],
                                  ["Username","Họ tên","Email","SĐT","GPLX","Thao tác"]):
                col.markdown(f"<div style='font-size:11px;color:#484f58;font-weight:700;"
                             f"text-transform:uppercase;padding:4px 0'>{label}</div>",
                             unsafe_allow_html=True)
            st.markdown("<hr style='border-color:#30363d;margin:4px 0 8px'>",
                        unsafe_allow_html=True)

            for u in users:
                c0, c1, c2, c3, c4, c5 = st.columns([2, 2.5, 2, 1.5, 1.5, 2])
                active_badge = (badge("Active","normal") if u["is_active"]
                                else badge("Inactive","tired"))
                c0.markdown(f"<span style='font-size:13px;color:#e6edf3'>"
                            f"@{u['username']}</span><br>{active_badge}",
                            unsafe_allow_html=True)
                c1.markdown(f"<span style='font-size:13px;color:#e6edf3'>"
                            f"{u['full_name']}</span>", unsafe_allow_html=True)
                c2.markdown(f"<span style='font-size:12px;color:#8b949e'>"
                            f"{u['email'] or '—'}</span>", unsafe_allow_html=True)
                c3.markdown(f"<span style='font-size:12px;color:#8b949e'>"
                            f"{u['phone'] or '—'}</span>", unsafe_allow_html=True)
                c4.markdown(f"<span style='font-size:12px;color:#8b949e'>"
                            f"{u['license_no'] or '—'}</span>", unsafe_allow_html=True)

                with c5:
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    with btn_col1:
                        if st.button("✏️", key=f"edit_{u['id']}", help="Sửa"):
                            st.session_state["edit_driver_id"] = u["id"]
                            st.session_state["show_edit_modal"] = True
                            st.rerun()
                    with btn_col2:
                        action = "🔴" if u["is_active"] else "🟢"
                        help_  = "Vô hiệu hóa" if u["is_active"] else "Kích hoạt"
                        if st.button(action, key=f"tog_{u['id']}", help=help_):
                            toggle_user_active(u["id"], not u["is_active"])
                            st.rerun()
                    with btn_col3:
                        if st.button("🗑️", key=f"del_{u['id']}", help="Xóa"):
                            st.session_state[f"confirm_del_{u['id']}"] = True
                            st.rerun()

                # Confirm delete
                if st.session_state.get(f"confirm_del_{u['id']}"):
                    st.warning(f"Xác nhận xóa **{u['full_name']}** (@{u['username']})?")
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        if st.button("✅ Xóa", key=f"yes_{u['id']}", type="primary"):
                            delete_user(u["id"])
                            del st.session_state[f"confirm_del_{u['id']}"]
                            st.success("Đã xóa.")
                            st.rerun()
                    with dc2:
                        if st.button("❌ Hủy", key=f"no_{u['id']}"):
                            del st.session_state[f"confirm_del_{u['id']}"]
                            st.rerun()
                st.markdown("<hr style='border-color:#1c2333;margin:4px 0'>",
                            unsafe_allow_html=True)

        # ── Edit modal (dùng expander giả modal) ──────────────
        if st.session_state.get("show_edit_modal") and st.session_state.get("edit_driver_id"):
            eid = st.session_state["edit_driver_id"]
            eu  = get_user(eid)
            if eu:
                with st.expander(f"✏️ Sửa thông tin: {eu['full_name']}", expanded=True):
                    with st.form(f"edit_form_{eid}"):
                        e1, e2 = st.columns(2)
                        fn  = e1.text_input("Họ và tên",    value=eu["full_name"])
                        em  = e2.text_input("Email",         value=eu["email"] or "")
                        ph  = e1.text_input("Số điện thoại",value=eu["phone"] or "")
                        ln  = e2.text_input("Số GPLX",      value=eu["license_no"] or "")
                        s1, s2 = st.columns(2)
                        saved   = s1.form_submit_button("💾 Lưu", type="primary")
                        cancel  = s2.form_submit_button("❌ Hủy")

                    if saved:
                        update_user(eid, fn, em, ph, ln)
                        st.session_state.pop("show_edit_modal", None)
                        st.session_state.pop("edit_driver_id", None)
                        st.success("Đã cập nhật.")
                        st.rerun()
                    if cancel:
                        st.session_state.pop("show_edit_modal", None)
                        st.session_state.pop("edit_driver_id", None)
                        st.rerun()

    # ════════════════════════════════════════════════════════
    #  Tab 2 – Thêm mới
    # ════════════════════════════════════════════════════════
    with tabs[1]:
        section_header("Thêm tài xế mới")
        with st.form("add_driver_form"):
            r1c1, r1c2 = st.columns(2)
            new_username = r1c1.text_input("Username *", placeholder="vd: driver03")
            new_fullname = r1c2.text_input("Họ và tên *", placeholder="Nguyễn Văn C")

            r2c1, r2c2 = st.columns(2)
            new_pw   = r2c1.text_input("Mật khẩu *", type="password", placeholder="••••••••")
            new_pw2  = r2c2.text_input("Nhập lại *",  type="password", placeholder="••••••••")

            r3c1, r3c2 = st.columns(2)
            new_email = r3c1.text_input("Email")
            new_phone = r3c2.text_input("Số điện thoại")

            r4c1, r4c2 = st.columns(2)
            new_license = r4c1.text_input("Số GPLX")
            new_role = r4c2.selectbox("Vai trò", ["driver", "admin"])

            submitted = st.form_submit_button("➕ Thêm tài xế", type="primary")

        if submitted:
            errs = []
            if not new_username: errs.append("Username không được trống.")
            if not new_fullname: errs.append("Họ tên không được trống.")
            if not new_pw:       errs.append("Mật khẩu không được trống.")
            if new_pw != new_pw2: errs.append("Mật khẩu nhập lại không khớp.")
            if len(new_pw) < 6:  errs.append("Mật khẩu tối thiểu 6 ký tự.")

            if errs:
                for e in errs:
                    st.error(e)
            else:
                try:
                    create_user(new_username, new_pw, new_role,
                                new_fullname, new_email, new_phone, new_license)
                    st.success(f"✅ Đã thêm tài xế **{new_fullname}** (@{new_username})")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi: {e} — Username có thể đã tồn tại.")
