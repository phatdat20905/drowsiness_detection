# views/profile_page.py  –  Hồ sơ cá nhân
import streamlit as st
from components.styles import inject_css, section_header, page_header, badge
from database.db import update_user, change_password, authenticate, get_user


def render():
    inject_css()
    user = st.session_state.user
    uid  = user["id"]

    page_header("👤 Hồ sơ cá nhân", "Xem và cập nhật thông tin tài khoản")

    tabs = st.tabs(["📋  Thông tin", "🔑  Đổi mật khẩu"])

    # ════════════════════════════════════════════════════════
    #  Tab 1 – Thông tin
    # ════════════════════════════════════════════════════════
    with tabs[0]:
        col_info, col_form = st.columns([1, 2], gap="large")

        # ── Avatar card ───────────────────────────────────────
        with col_info:
            role_badge = (badge("Admin", "admin") if user["role"] == "admin"
                          else badge("Tài xế", "driver"))
            st.markdown(f"""
            <div style="background:#1c2333;border:1px solid #30363d;
                        border-radius:14px;padding:28px 24px;text-align:center;">
                <div style="font-size:4rem;margin-bottom:14px;">
                    {'👑' if user['role'] == 'admin' else '🚘'}
                </div>
                <div style="font-size:17px;font-weight:700;color:#e6edf3;margin-bottom:4px;">
                    {user.get('full_name','—')}
                </div>
                <div style="font-size:13px;color:#8b949e;margin-bottom:12px;">
                    @{user.get('username','')}
                </div>
                {role_badge}
                <hr style="border-color:#30363d;margin:18px 0 14px;">
                <div style="text-align:left;font-size:12px;color:#8b949e;line-height:2.2;">
                    📧 {user.get('email','—') or '—'}<br>
                    📞 {user.get('phone','—') or '—'}<br>
                    🪪 {user.get('license_no','—') or '—'}<br>
                    🗓️ Tham gia: {str(user.get('created_at',''))[:10]}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Edit form ─────────────────────────────────────────
        with col_form:
            section_header("Cập nhật thông tin")
            with st.form("profile_form"):
                fn  = st.text_input("Họ và tên",
                                    value=user.get("full_name", ""))
                c1, c2 = st.columns(2)
                em  = c1.text_input("Email",
                                    value=user.get("email", "") or "")
                ph  = c2.text_input("Số điện thoại",
                                    value=user.get("phone", "") or "")
                ln  = st.text_input("Số GPLX",
                                    value=user.get("license_no", "") or "")

                saved = st.form_submit_button("💾 Lưu thay đổi",
                                              type="primary",
                                              use_container_width=True)

            if saved:
                if not fn.strip():
                    st.error("Họ tên không được trống.")
                else:
                    update_user(uid, fn, em, ph, ln)
                    # Refresh session_state
                    fresh = get_user(uid)
                    st.session_state.user = dict(fresh)
                    st.success("✅ Đã cập nhật thông tin.")
                    st.rerun()

    # ════════════════════════════════════════════════════════
    #  Tab 2 – Đổi mật khẩu
    # ════════════════════════════════════════════════════════
    with tabs[1]:
        section_header("Đổi mật khẩu")

        _, col_pw, _ = st.columns([1, 2, 1])
        with col_pw:
            with st.form("pw_form"):
                old_pw  = st.text_input("Mật khẩu hiện tại", type="password",
                                        placeholder="••••••••")
                new_pw  = st.text_input("Mật khẩu mới", type="password",
                                        placeholder="Tối thiểu 6 ký tự")
                new_pw2 = st.text_input("Nhập lại mật khẩu mới", type="password",
                                        placeholder="••••••••")
                change_btn = st.form_submit_button("🔑 Đổi mật khẩu",
                                                   type="primary",
                                                   use_container_width=True)

            if change_btn:
                errs = []
                if not old_pw:
                    errs.append("Nhập mật khẩu hiện tại.")
                elif not authenticate(user["username"], old_pw):
                    errs.append("Mật khẩu hiện tại không đúng.")
                if len(new_pw) < 6:
                    errs.append("Mật khẩu mới tối thiểu 6 ký tự.")
                if new_pw != new_pw2:
                    errs.append("Mật khẩu nhập lại không khớp.")
                if new_pw == old_pw:
                    errs.append("Mật khẩu mới phải khác mật khẩu cũ.")

                if errs:
                    for e in errs:
                        st.error(e)
                else:
                    change_password(uid, new_pw)
                    st.success("✅ Đổi mật khẩu thành công. Vui lòng đăng nhập lại.")
                    st.session_state.clear()
                    st.rerun()

            st.markdown("""
            <div style="margin-top:16px;padding:12px 14px;background:#1c2333;
                        border:1px solid #30363d;border-radius:10px;
                        font-size:12px;color:#8b949e;line-height:1.8;">
                <b style="color:#e6edf3;">Yêu cầu mật khẩu:</b><br>
                • Tối thiểu 6 ký tự<br>
                • Khác mật khẩu hiện tại<br>
                • Sau khi đổi, hệ thống sẽ đăng xuất tự động
            </div>""", unsafe_allow_html=True)
