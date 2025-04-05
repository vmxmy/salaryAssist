import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
from fiscal_report_full_script import process_sheet, format_excel_with_styles
import json
import matplotlib.pyplot as plt
import numpy as np # 确保导入 numpy

# --- Matplotlib 中文显示设置 ---
# 使用从系统中找到的字体，优先 Lantinghei SC
plt.rcParams['font.sans-serif'] = ['Lantinghei SC', 'SimSong', 'Kaiti SC', 'Songti SC', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
# --- 结束设置 ---

# --- 初始化 Session State ---
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'mapping_data' not in st.session_state:
    st.session_state.mapping_data = None
if 'mapping_valid' not in st.session_state:
    st.session_state.mapping_valid = None # None: 未上传, True: 有效, False: 无效
# --- 结束初始化 ---

# --- 日志记录函数 ---
def log(message, level="INFO"):
    now = datetime.now().strftime("%H:%M:%S")
    level_icon_map = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅"}
    icon = level_icon_map.get(level, "▪️")
    log_level_class = f"log-{level.lower()}"

    # Wrap prefix and message in spans for styling
    formatted_message = f"<span class='log-prefix'>{now} {icon}</span> <span class='{log_level_class}'>{message}</span>"

    st.session_state.log_messages.append(formatted_message)
    # 注意：日志在侧边栏的更新通常在整个按钮脚本执行完后发生
# --- 结束日志函数 ---

st.set_page_config(layout="wide", page_title="财政工资处理系统")

# --- NEW CSS for Modern Minimalist Style ---
modern_minimalist_css = """
<style>
/* Import Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

/* Global Styles */
html, body, [class*="st-"] {{
    font-family: 'Inter', sans-serif;
    background-color: #F8F9FA; /* Light grey background */
    color: #212529; /* Dark text */
}}

/* Sidebar Styles */
[data-testid="stSidebar"] {{
    background-color: #FFFFFF; /* White sidebar */
    border-right: 1px solid #E0E0E0; /* Subtle border */
    box-shadow: 2px 0px 5px rgba(0, 0, 0, 0.05); /* Slight shadow */
}}

/* Titles and Headers */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Inter', sans-serif;
    font-weight: 600; /* Bolder headers */
}}

/* Custom simple subheader style (replaces old .custom-subheader) */
.simple-subheader {{
    font-size: 1.5em; /* H3 size equivalent */
    font-weight: 600;
    margin-top: 25px;
    margin-bottom: 15px;
    border-bottom: 1px solid #E0E0E0; /* Subtle underline */
    padding-bottom: 8px;
}}

/* Input Controls */
[data-testid="stTextInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stSelectbox"] div[role="combobox"] {{
    border: 1px solid #ced4da;
    border-radius: 0.3rem;
    background-color: #FFFFFF;
}}

/* File Uploader Adjustments */
[data-testid="stFileUploader"] {{
    /* Add some space */
    margin-bottom: 10px;
}}

/* Primary Button Styling */
button[kind="primary"] {{
    background-color: #0d6efd; /* Primary blue */
    color: white;
    padding: 0.75rem 1.25rem; /* Moderate padding */
    font-size: 1rem; /* Standard font size */
    font-weight: 600;
    border-radius: 0.3rem; /* Consistent rounding */
    border: none; /* Remove default border */
    transition: background-color 0.2s ease-in-out; /* Hover effect */
}}

button[kind="primary"]:hover {{
    background-color: #0b5ed7; /* Darker blue on hover */
}}

/* Log Message Styling */
.log-info {{ color: #0dcaf0; }} /* Cyan info */
.log-warning {{ color: #ffc107; }} /* Yellow warning */
.log-error {{ color: #dc3545; font-weight: bold; }} /* Red, bold error */
.log-success {{ color: #198754; }} /* Green success */

/* Styling for the log timestamp and icon */
.log-prefix {{
    color: #6c757d; /* Grey for timestamp/icon */
    margin-right: 5px;
}}

/* Adjust log container in sidebar */
[data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stVerticalBlock"] {{
     /* Potentially adjust padding or spacing if needed */
}}

</style>
"""
st.markdown(modern_minimalist_css, unsafe_allow_html=True)

# --- 旧 CSS (注释掉或删除) ---
# styled_header_css = """
# <style>
# .custom-subheader {
#     border-left: 5px solid #1E90FF; /* Dodger blue left border */
#     background-color: #F0F8FF; /* Alice blue background */
#     padding: 10px 15px;      /* Padding around text */
#     margin-top: 20px;         /* Space above */
#     margin-bottom: 15px;      /* Space below */
#     border-radius: 5px;       /* Rounded corners */
#     font-size: 1.75em;        /* H3 font size */
#     line-height: 1.4;         /* Adjust line height */
#     font-weight: 600;         /* Make it bolder like headers */
# }
# /* Ensure the text inside aligns well, prevent potential default margins */
# .custom-subheader h3 {
#     margin: 0;
#     padding: 0;
#     line-height: inherit; /* Inherit line height */
#     font-size: inherit; /* Inherit font size */
#     font-weight: inherit; /* Inherit font weight */
# }
#
# /* Target Streamlit's primary button to make it larger */
# button[kind="primary"] {
#     padding: 15px 30px; /* Further increase padding */
#     font-size: 2.4em;  /* Further increase font size */
#     font-weight: bold; /* Ensure font is bold */
# }
# </style>
# """
# st.markdown(styled_header_css, unsafe_allow_html=True)

# --- 主界面 ---
st.title("成都高新区财金局 工资条数据处理与合并工具")

# --- 表单输入区域 ---
st.sidebar.header("🔧 参数设置")

# 自定义单位名称
unit_name = st.sidebar.text_input("单位名称", value="高新区财政局")

# 日期控件（默认当前月份）
def_year = datetime.today().year
def_month = datetime.today().month

salary_date = st.sidebar.date_input("工资表日期（用于标题栏）", value=datetime(def_year, def_month, 1), format="YYYY-MM-DD")

# --- 日志显示区域 ---
with st.sidebar.expander("📄 处理日志", expanded=True):
    log_container = st.container(height=300) # 固定高度可滚动容器
    with log_container:
        for message in st.session_state.log_messages:
            st.markdown(message, unsafe_allow_html=True) # Markdown is now expected to contain spans like <span class='log-info'>...</span>
# --- 结束日志显示 ---

# 文件上传
st.markdown("<p class='simple-subheader'>📁 上传所需文件</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    # 使用 markdown 作为标签，并隐藏 file_uploader 自带的标签
    st.caption("📎 源数据工资表（支持多文件）")
    source_files = st.file_uploader("source_uploader", type=["xlsx"], accept_multiple_files=True, label_visibility="collapsed", key="source_uploader")

    st.caption("📎 导出表字段模板")
    file_template = st.file_uploader("template_uploader", type=["xlsx"], label_visibility="collapsed", key="template_uploader")

with col2:
    st.caption("📎 扣款项表（含姓名+各项扣款）")
    file_deductions = st.file_uploader("deductions_uploader", type=["xlsx"], label_visibility="collapsed", key="deductions_uploader")

    st.caption("📎 字段映射规则 （JSON格式）")
    file_mapping = st.file_uploader("mapping_uploader", type=["json"], label_visibility="collapsed", key="mapping_uploader")

# --- JSON 校验逻辑 ---
# 每次脚本运行时都重新校验上传的文件状态
mapping_validation_placeholder = st.empty() # 用于显示校验结果消息
temp_mapping_data = None
if file_mapping is not None:
    try:
        # 重置文件读取指针
        file_mapping.seek(0)
        # 尝试解析 JSON
        temp_mapping_data = json.load(file_mapping)
        # 基本结构检查 (确保顶层是对象，且包含 'field_mappings' 列表)
        if isinstance(temp_mapping_data, dict) and isinstance(temp_mapping_data.get('field_mappings'), list):
            # 只有当新上传的文件有效时才更新 session_state
            st.session_state.mapping_data = temp_mapping_data
            st.session_state.mapping_valid = True
            mapping_validation_placeholder.success("✅ 映射文件 JSON 有效。")
        else:
            st.session_state.mapping_valid = False # 标记为无效，但不清除可能存在的旧有效数据
            mapping_validation_placeholder.error("❌ JSON 文件顶层结构错误：需要包含 'field_mappings' 列表。")
            # 可选：清除旧数据 st.session_state.mapping_data = None

    except json.JSONDecodeError as e:
        st.session_state.mapping_valid = False
        mapping_validation_placeholder.error(f"❌ 映射文件 JSON 语法错误：\n在行 {e.lineno} 列 {e.colno} 附近: {e.msg}")
        # 可选：清除旧数据 st.session_state.mapping_data = None
    except Exception as e: # 捕获其他可能的读取错误
        st.session_state.mapping_valid = False
        mapping_validation_placeholder.error(f"❌ 读取或解析映射文件时出错: {e}")
        # 可选：清除旧数据 st.session_state.mapping_data = None
else:
    # 如果 file_mapping 控件中没有文件（例如用户清除了上传），也应更新状态
    # 如果希望保留上次有效上传的数据，可以注释掉下面两行
    # st.session_state.mapping_data = None
    st.session_state.mapping_valid = None # 设为 None 表示未上传状态
# --- 结束 JSON 校验 ---

# 从 session_state 获取数据，如果无效或为 None 则用空字典
mapping_data_from_state = st.session_state.get('mapping_data') or {}
field_mappings = mapping_data_from_state.get('field_mappings', [])

# --- 确保 template_fields 和 sample_source_fields 在此处被无条件初始化 ---
template_fields = []
sample_source_fields = set()
# --- 结束无条件初始化 ---

# 模板字段名预取
if file_template:
    try:
        file_template.seek(0)
        template_df_header = pd.read_excel(file_template, skiprows=2, nrows=1)
        template_fields = template_df_header.columns.tolist()
    except Exception as e:
        st.warning(f"模板字段读取失败：{e}")

# 源数据字段示例收集
if source_files:
    try:
        uploaded_source_file = source_files[0]
        uploaded_source_file.seek(0)
        source_preview = pd.read_excel(uploaded_source_file, nrows=10, header=None)
        # 修复括号和逻辑：查找包含'姓名'或'人员姓名'的行
        header_row = next((i for i, row in source_preview.iterrows() if any(("姓名" in str(cell)) or ("人员姓名" in str(cell)) for cell in row.astype(str))), None)
        if header_row is not None:
            # 重置指针，读取正确的表头行
            uploaded_source_file.seek(0)
            df_source_cols = pd.read_excel(uploaded_source_file, skiprows=header_row, nrows=0).columns.tolist() # nrows=0 也可以读表头
            sample_source_fields = set(df_source_cols)
        else:
            st.warning("无法在第一个源文件中自动检测表头行以获取示例字段。")
    except Exception as e:
        st.warning(f"读取源数据示例字段时出错: {e}")

# --- 规则匹配设置 --- #
st.markdown("<p class='simple-subheader'>🔀 字段匹配关系设置</p>", unsafe_allow_html=True)
# 只保留一个选择框，因为源文件和规则使用相同字段名
# 使用 sample_source_fields (确保它已定义并可能是 set)
source_cols_list = sorted(list(sample_source_fields)) if sample_source_fields else []
identity_column_name_select = st.selectbox(
    "选择用于匹配规则的字段名", # 修改标签
    options=source_cols_list,
    index=source_cols_list.index("人员身份") if "人员身份" in source_cols_list else (source_cols_list.index("岗位类别") if "岗位类别" in source_cols_list else 0), # 尝试默认 人员身份 或 岗位类别
    help="选择源文件和JSON规则中都使用的那个字段名进行匹配（如 人员身份, 岗位类别）" # 修改帮助文本
)
# --- 结束规则匹配设置 --- #

# 只有当映射文件有效时才显示编辑和可视化区域
if st.session_state.get('mapping_valid') is True:
    with st.expander("📋 映射规则编辑与可视化（支持新增/校验/下载）", expanded=False):
        # 可视化字段映射统计
        field_count = {"有效映射": 0, "源字段缺失": 0, "目标字段缺失": 0}
        missing_source_details = [] # 用于存储缺失源字段的详细信息
        missing_target_details = [] # 用于存储缺失目标字段的详细信息

        # 确保 current_sample_source_fields 在这里可用
        current_sample_source_fields = sample_source_fields

        for rule in field_mappings:
            # 获取当前规则的标识符，用于日志/错误信息
            # 使用用户在 selectbox 中选择的字段名
            rule_identity_value = rule.get(identity_column_name_select, "未知规则标识")

            for mapping in rule.get("mappings", []):
                src = mapping.get("source_field", "")
                tgt = mapping.get("target_field", "")

                # 只对简单映射进行源/目标字段校验
                if "source_field" in mapping:
                    is_valid = False # 标记当前映射是否有效
                    # 检查源字段是否存在
                    if src not in current_sample_source_fields:
                        field_count["源字段缺失"] += 1
                        missing_source_details.append({
                            "rule_id": rule_identity_value,
                            "source": src,
                            "target": tgt
                        })
                    # 如果源字段存在，再检查目标字段 (如果模板存在)
                    else:
                        # 检查目标字段是否在模板中 (仅当 template_fields 非空时)
                        if template_fields and (tgt not in template_fields):
                            field_count["目标字段缺失"] += 1
                            missing_target_details.append({
                                "rule_id": rule_identity_value,
                                "source": src,
                                "target": tgt
                            })
                        else:
                             # 源字段存在，且(无模板 或 目标字段在模板中)
                             field_count["有效映射"] += 1
                             is_valid = True
                    # (注意: 复杂映射 ("source_fields") 不在此处校验源/目标字段是否存在)

        # 条形图展示映射校验结果
        st.markdown("#### 映射校验统计图")
        try:
            fig, ax = plt.subplots()
            bars = ax.bar(field_count.keys(), field_count.values(), color=["green", "orange", "red"])
            ax.bar_label(bars) # 在条形图上显示数值
            ax.set_title("字段映射状态统计")
            st.pyplot(fig)
        except Exception as plot_err:
            st.error(f"绘制图表时出错: {plot_err}")

        # --- 显示缺失字段详情 --- #
        st.markdown("--- impunity") # 分隔线
        if missing_source_details:
            st.error("**源字段缺失详情 (请检查源文件或映射规则):**")
            for detail in missing_source_details:
                st.markdown(f"- 规则 **'{detail['rule_id']}'**: 源字段 `'{detail['source']}'` (映射到 `'{detail['target']}'`) 在示例源文件中未找到。")

        if missing_target_details:
            st.warning("**目标字段缺失详情 (与模板文件对比):**")
            for detail in missing_target_details:
                st.markdown(f"- 规则 **'{detail['rule_id']}'**: 目标字段 `'{detail['target']}'` (来自 `'{detail['source']}'`) 在模板文件中未找到。")
        # --- 结束详情显示 --- #

        # 映射编辑
        for i, rule in enumerate(field_mappings):
            st.markdown(f"**人员身份：{rule.get('人员身份', '')} | 编制：{rule.get('编制', '')}**")
            for j, mapping in enumerate(rule.get("mappings", [])):
                if "source_field" in mapping:
                    col1, col2 = st.columns(2)
                    with col1:
                        mapping["source_field"] = st.text_input(f"源字段 #{i}-{j}", mapping.get("source_field", ""), key=f"src_{i}_{j}")
                    with col2:
                        mapping["target_field"] = st.text_input(f"目标字段 #{i}-{j}", mapping.get("target_field", ""), key=f"tgt_{i}_{j}_simple")
                elif "source_fields" in mapping:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**计算规则 #{i}-{j}**")
                        st.caption(f"源字段组: `{', '.join(mapping.get('source_fields', []))}`")
                        st.caption(f"计算方式: `{mapping.get('calculation', '')}`")
                    with col2:
                         mapping["target_field"] = st.text_input(f"目标字段 #{i}-{j}", mapping.get("target_field", ""), key=f"tgt_{i}_{j}_complex")
                else:
                    st.warning(f"规则 {i}-{j} 格式无法识别: {mapping}")

        # --- 新增映射规则表单 (移除内层 Expander) ---
        st.markdown("--- impunity") # 添加分隔线
        st.markdown("**➕ 添加新的人员身份映射**") # 使用 markdown 作为标题
        # 反向缩进以下内容
        new_identity = st.text_input("人员身份", key="new_identity_inp") # 避免 key 冲突
        new_bianzhi = st.text_input("编制", key="new_bianzhi_inp")
        new_source = st.text_input("源字段名", key="new_source_inp")
        new_target = st.text_input("目标字段名", key="new_target_inp")
        if st.button("添加映射规则", key="add_mapping_btn"):
            # 查找人员身份键，需要考虑用户选择的 rule_identity_key_select
            # 暂时硬编码检查 '人员身份'，但理想情况应使用选择的 key
            match_key = "人员身份" # 或者 rule_identity_key_select (需要从外部传入或session state获取)
            if not new_identity: # 假设新规则基于"人员身份"添加
                 st.warning("请输入要添加规则的'人员身份'值", icon="⚠️")
            elif not new_source or not new_target:
                 st.warning("请输入源字段名和目标字段名", icon="⚠️")
            else:
                new_rule = next((r for r in field_mappings if r.get(match_key) == new_identity), None)
                if not new_rule:
                    new_rule = {match_key: new_identity, "编制": new_bianzhi, "mappings": []}
                    # 注意：直接修改 field_mappings 可能在 rerun 后丢失，需要更新 session_state
                    field_mappings.append(new_rule)
                    # 更新 session state (重要!)
                    if st.session_state.mapping_data:
                         st.session_state.mapping_data['field_mappings'] = field_mappings
                new_rule["mappings"].append({"source_field": new_source, "target_field": new_target})
                st.success("✅ 新映射已添加 (请记得下载保存)")
                st.experimental_rerun() # 添加映射后需要重新运行以更新显示
        # --- 结束新增表单 ---

        # 下载保存
        edited_json_for_download = json.dumps({"field_mappings": field_mappings}, ensure_ascii=False, indent=2)
        st.download_button("📥 下载当前映射规则 JSON", edited_json_for_download, file_name="字段映射规则_编辑版.json", mime="application/json")

        if st.button("💾 保存映射规则到服务器（模拟）"):
            save_path = "./映射规则_保存备份.json"
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(edited_json_for_download)
                st.success(f"已保存到：{save_path}")
            except Exception as save_err:
                st.error(f"保存文件时出错: {save_err}")

# --- 处理触发区域 ---
st.markdown("---") # 分隔线

if st.button("🚀 开始处理数据", type="primary"):
    # 清空旧日志并记录开始
    st.session_state.log_messages = []
    log("开始处理流程...", "INFO")

    # 1. 输入校验
    valid_inputs = True
    if not source_files:
        log("请至少上传一个源数据工资表！", "ERROR")
        valid_inputs = False
    if not file_deductions:
        log("请上传扣款项表！", "ERROR")
        valid_inputs = False
    if not st.session_state.get('mapping_valid', False):
        log("字段映射文件无效或未上传！", "ERROR")
        valid_inputs = False
    if not identity_column_name_select:
        log("请选择用于匹配规则的字段名！", "ERROR")
        valid_inputs = False

    if valid_inputs:
        # 2. 准备数据
        deduction_df = None
        current_field_mappings = st.session_state.get('mapping_data', {}).get('field_mappings', [])
        selected_deduction_fields = [] # 初始化

        try:
            log("读取扣款数据...", "INFO")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_deduct:
                file_deductions.seek(0)
                tmp_deduct.write(file_deductions.getvalue())
                tmp_deduct_path = tmp_deduct.name
            try:
                deduction_df = pd.read_excel(tmp_deduct_path)
            finally:
                os.unlink(tmp_deduct_path)

            # 校验扣款表姓名列
            key_col_found = False
            name_columns = ["姓名", "人员姓名"]
            actual_name_col = None
            for key_col in name_columns:
                if key_col in deduction_df.columns:
                    key_col_found = True
                    actual_name_col = key_col # 记录找到的姓名列
                    break
            if not key_col_found:
                log(f"扣款表必须包含 '姓名' 或 '人员姓名' 列！", "ERROR")
                st.stop()
            else:
                log(f"扣款数据读取成功，找到键列: '{actual_name_col}'。", "INFO")

            # 自动确定扣款字段列表
            all_deduction_cols = deduction_df.columns.tolist()
            selected_deduction_fields = [col for col in all_deduction_cols if col != actual_name_col]
            log(f"自动识别用于合并的扣款字段 (共 {len(selected_deduction_fields)} 个): {selected_deduction_fields}", "INFO")
            if not selected_deduction_fields:
                 log("警告：扣款表中除了姓名列外未找到其他字段。", "WARNING")

            # 3. 处理每个源文件
            all_results = []
            has_error = False
            log(f"开始逐个处理 {len(source_files)} 个源文件... (使用 '{identity_column_name_select}' 字段匹配)", "INFO")
            with st.spinner(f"正在处理 {len(source_files)} 个源文件..."):
                for i, uploaded_file in enumerate(source_files):
                    log(f"[{i+1}/{len(source_files)}] 处理文件: {uploaded_file.name}", "INFO")
                    tmp_source_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_source:
                            tmp_source.write(uploaded_file.getvalue())
                            tmp_source_path = tmp_source.name

                        # 添加调用 process_sheet 的日志
                        log(f"  -> 调用核心处理函数 process_sheet...", "INFO")
                        result_df = process_sheet(
                            tmp_source_path,
                            deduction_df,
                            current_field_mappings,
                            selected_deduction_fields,
                            identity_column_name_select,
                            identity_column_name_select
                         )
                        log(f"  <- process_sheet 返回，结果行数: {len(result_df) if result_df is not None else 'None'}", "INFO")
                        if result_df is not None and not result_df.empty:
                             all_results.append(result_df)
                             log(f"[{i+1}/{len(source_files)}] 文件 {uploaded_file.name} 处理成功。", "SUCCESS")
                        else:
                             log(f"[{i+1}/{len(source_files)}] 文件 {uploaded_file.name} 未返回有效数据 (可能无匹配行或处理错误)。", "WARNING")

                    except ValueError as ve: # 捕获 process_sheet 返回的特定错误？还是内部处理？
                        # 假设 process_sheet 内部已打印错误，这里只记录失败
                        log(f"[{i+1}/{len(source_files)}] 文件 {uploaded_file.name} 处理失败。", "ERROR")
                        has_error = True
                    except Exception as e:
                        log(f"[{i+1}/{len(source_files)}] 处理文件 {uploaded_file.name} 时发生意外错误: {e}", "ERROR")
                        has_error = True
                    finally:
                        if tmp_source_path and os.path.exists(tmp_source_path):
                           os.unlink(tmp_source_path)
                    if has_error:
                         log(f"因处理文件 {uploaded_file.name} 时发生错误，处理中止。", "ERROR")
                         break # 保持中止逻辑

            # 4. 合并与格式化
            if not has_error and all_results:
                log("所有文件处理完成，开始合并 {len(all_results)} 个结果...", "INFO")
                with st.spinner("合并结果并格式化输出..."):
                    tmp_processed_path = None
                    output_path = None
                    try:
                        combined_df = pd.concat(all_results, ignore_index=True)
                        log("结果合并完成，总行数: {len(combined_df)}", "INFO")

                        if file_template and template_fields:
                            # 恢复为严格按模板 reindex，丢弃不在模板中的列
                            log(f"根据模板文件的 {len(template_fields)} 个字段严格筛选和排序输出列...", "INFO")
                            combined_df = combined_df.reindex(columns=template_fields)
                            # 注意：如果 template_fields 包含 combined_df 中没有的列，reindex 会添加它们并填充 NaN
                        else:
                             log("未提供模板文件或读取失败，按原始处理顺序输出所有列。", "INFO")

                        log("保存处理结果到临时文件...", "INFO")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_processed:
                            combined_df.to_excel(tmp_processed.name, index=False)
                            tmp_processed_path = tmp_processed.name

                        output_filename = f"{unit_name}_{salary_date.strftime('%Y%m')}_工资发放表_已处理.xlsx"
                        output_dir = tempfile.mkdtemp()
                        output_path = os.path.join(output_dir, output_filename)

                        log("开始格式化输出文件...", "INFO")
                        format_excel_with_styles(tmp_processed_path, output_path, salary_date.year, salary_date.month)
                        log("文件格式化完成。", "SUCCESS")

                        # 5. 提供下载
                        # st.success(f"🎉 处理完成！...") # 由 log 替代
                        log(f"处理成功完成！最终报告已生成：{output_filename}", "SUCCESS")
                        with open(output_path, "rb") as fp:
                            st.download_button(
                                label="📥 下载最终报告",
                                data=fp,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_report"
                            )

                    except Exception as e:
                        log(f"合并或格式化 Excel 文件时出错: {e}", "ERROR")
                        has_error = True # 确保标记错误
                    finally:
                        if tmp_processed_path and os.path.exists(tmp_processed_path):
                            os.unlink(tmp_processed_path)

            elif not all_results and not has_error:
                 log("未生成任何有效数据，请检查源文件内容和映射规则。", "WARNING")
            elif has_error:
                log("处理因发生错误而中止。", "ERROR")

        except Exception as e:
            log(f"处理过程中发生无法恢复的严重错误: {e}", "ERROR")
            # 确保清理可能遗留的临时文件
            if 'tmp_deduct_path' in locals() and os.path.exists(tmp_deduct_path):
                os.unlink(tmp_deduct_path)
            if 'tmp_source_path' in locals() and os.path.exists(tmp_source_path):
                os.unlink(tmp_source_path)
            if 'tmp_processed_path' in locals() and os.path.exists(tmp_processed_path):
                os.unlink(tmp_processed_path)

    else:
        log("输入校验失败，请检查上传的文件和配置。", "ERROR")

# 可以添加页脚等信息
st.markdown("---")
st.caption("© 成都高新区财政金融局")
