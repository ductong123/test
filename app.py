import streamlit as st
import pandas as pd
import numpy_financial as npf
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


st.set_page_config(page_title="Đánh giá đầu tư BĐS", layout="wide")
st.title("🏘️ Hệ thống đánh giá hiệu quả đầu tư Bất động sản")
st.markdown("**Tải file Excel và thiết lập các thông số ở thanh bên trái.**")

# Sidebar nhập liệu
with st.sidebar:
    st.header("⚙️ Cài đặt đầu tư")
    uploaded_file = st.file_uploader("📥 Tải lên file Excel danh sách căn hộ", type=["csv"])
    discount_rate = st.number_input("📉 Tỷ lệ chiết khấu (%)", 0.0, 50.0, 10.0) / 100
    rental_yield = st.number_input("💸 Tỷ suất lợi nhuận cho thuê (%)", 0.0, 20.0, 5.0) / 100
    years = st.slider("📅 Số năm đầu tư", 1, 30, 5)

# Hàm tính toán
def calculate_npv(rate, cash_flows):
    return npf.npv(rate, cash_flows)

def calculate_irr(cash_flows):
    return npf.irr(cash_flows)

# Highlight màu trong bảng
def highlight_columns(s):
    color_red = 'background-color: #ffdddd'
    color_green = 'background-color: #ddffdd'
    if s.name == "NPV (VND)":
        return [color_green if v > 0 else color_red for v in s]
    elif s.name == "IRR (%)":
        return [color_green if v > discount_rate * 100 else color_red for v in s]
    elif s.name == "Gợi ý":
        return [color_green if "Nên" in v else color_red for v in s]
    else:
        return [''] * len(s)

# Khi có file được upload
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()  # Xóa khoảng trắng thừa trong tên cột

    required_cols = ["Mã Căn", "View", "Tổng Giá Đã Trừ KM", "Diện Tích (m2)"]
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        st.error(f"⚠️ File thiếu cột: {missing}")
    else:
        # Tính toán
        results = []
        for idx, row in df.iterrows():
            code = row["Mã Căn"]
            view = row["View"]
            area = row["Diện Tích (m2)"]
            investment = -row["Tổng Giá Đã Trừ KM"]
            annual_income = -investment * rental_yield
            cash_flows = [investment] + [annual_income] * years
            npv = calculate_npv(discount_rate, cash_flows)
            irr = calculate_irr(cash_flows)
            decision = "✅ Nên đầu tư" if npv > 0 and irr > discount_rate else "❌ Không nên đầu tư"

            results.append({
                "Mã Căn": code,
                "View": view,
                "Diện Tích (m2)": area,
                "Vốn đầu tư (VND)": abs(investment),
                "Thu nhập/năm (VND)": abs(annual_income),
                "NPV (VND)": npv,
                "IRR (%)": irr * 100,
                "Gợi ý": decision
            })

        result_df = pd.DataFrame(results)

        # 🔝 Hiển thị bảng kết quả
        st.subheader("📋 Bảng đánh giá đầu tư các căn hộ")
        st.dataframe(
            result_df.style
                .format({
                    "Diện Tích (m2)": "{:.2f}",
                    "Vốn đầu tư (VND)": "{:,.0f}",
                    "Thu nhập/năm (VND)": "{:,.0f}",
                    "NPV (VND)": "{:,.0f}",
                    "IRR (%)": "{:.2f}"
                })
                .apply(highlight_columns, axis=0),
            use_container_width=True,
            height=len(result_df) * 35
        )

        # 🔽 Chi tiết dòng tiền căn hộ
        st.markdown("---")
        st.subheader("🔍 Xem chi tiết dòng tiền của từng căn")

        selected_code = st.selectbox("Chọn mã căn để xem dòng tiền chi tiết", result_df["Mã Căn"].tolist())

        if selected_code:
            selected_row = df[df["Mã Căn"] == selected_code].iloc[0]
            investment = -selected_row["Tổng Giá Đã Trừ KM"]
            annual_income = -investment * rental_yield
            area = selected_row["Diện Tích (m2)"]
            cash_flows = [investment] + [annual_income] * years
            labels = ["Năm 0"] + [f"Năm {i}" for i in range(1, years + 1)]

            npv = calculate_npv(discount_rate, cash_flows)
            irr = calculate_irr(cash_flows)

            st.markdown(f"### 📌 Chi tiết căn **{selected_code}** - View: **{selected_row['View']}**")
            st.write(f"- **Diện tích:** {area:.2f} m²")
            st.write(f"- **Vốn đầu tư ban đầu:** {abs(investment):,.0f} VND")
            st.write(f"- **Thu nhập mỗi năm:** {abs(annual_income):,.0f} VND")
            st.write(f"- **NPV:** {npv:,.0f} VND")
            st.write(f"- **IRR:** {irr*100:.2f}%")

            # Biểu đồ dòng tiền
            st.markdown("#### 📊 Biểu đồ dòng tiền")
            fig, ax = plt.subplots(figsize=(15, 10))
            bars = ax.bar(labels, cash_flows, color=['#E74C3C'] + ['#2ECC71'] * years, width=0.4)
            ax.axhline(0, color='black', linestyle='--', linewidth=1)
            ax.set_title(f"Dòng tiền căn {selected_code}", fontsize=14)
            ax.set_ylabel("VND")
            ax.grid(axis='y', linestyle=':', alpha=0.7)

            # 👉 Định dạng trục y thành tiền tệ với + và - rõ ràng
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

            # 👉 Ghi số tiền trên mỗi cột
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:,.0f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 5 if height >= 0 else -15), textcoords="offset points",
                            ha='center', va='bottom', fontsize=9)

            st.pyplot(fig)

            

