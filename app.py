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
# --- 新增 Session State for Single Select --- #
if 'single_selected_identity_column' not in st.session_state:
    st.session_state.single_selected_identity_column = None
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

/* --- 更新：为默认按钮添加现代轮廓样式 --- */
button:not([kind="primary"]) {{
    background-color: transparent;
    color: #198754; /* Bootstrap success green */
    border: 1px solid #198754;
    padding: 0.75rem 1.25rem; /* Match primary button padding */
    font-size: 1rem; /* Match primary font size */
    font-weight: 600; /* Match primary font weight */
    border-radius: 0.5rem; /* Softer corners */
    transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}}

button:not([kind="primary"]):hover {{
    background-color: #198754; /* Fill with green on hover */
    color: white;
    border-color: #198754;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
}}
/* --- 结束更新 --- */

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
st.title("工资表合并AI助手")

# --- 表单输入区域 ---
st.sidebar.title("高新区财金局综合处")
st.sidebar.header("🔧 参数设置")

# 自定义单位名称
unit_name = st.sidebar.text_input("单位名称", value="高新区财政局")

# 日期控件（默认当前月份）
def_year = datetime.today().year
def_month = datetime.today().month

salary_date = st.sidebar.date_input("工资表日期（用于标题栏）", value=datetime(def_year, def_month, 1), format="YYYY-MM-DD")


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

# --- 新增：独立状态条 --- #
st.sidebar.subheader("📊 文件上传状态")

required_files_status = {
    "源数据工资表": bool(source_files),
    "扣款项表": bool(file_deductions),
    "字段映射规则": bool(file_mapping and st.session_state.get('mapping_valid') is True)
}
optional_files_status = {
    "导出表字段模板": bool(file_template)
}

# --- 新增：独立状态条 --- #
st.sidebar.markdown("**必需文件:**")
for file_name, is_uploaded in required_files_status.items():
    if is_uploaded:
        st.sidebar.success(f"✅ {file_name}")
    else:
        st.sidebar.warning(f"🟡 {file_name} (未上传)")

st.sidebar.markdown("**可选文件:**")
for file_name, is_uploaded in optional_files_status.items():
    if is_uploaded:
        st.sidebar.success(f"✅ {file_name} (可选)")
    else:
        st.sidebar.info(f"⚪️ {file_name} (可选, 未上传)")
# --- 结束新增 --- #

st.sidebar.markdown("---")

# --- 日志显示区域 ---
with st.sidebar.expander("📄 处理日志", expanded=True):
    log_container = st.container(height=300) # 固定高度可滚动容器
    with log_container:
        for message in st.session_state.log_messages:
            st.markdown(message, unsafe_allow_html=True) # Markdown is now expected to contain spans like <span class='log-info'>...</span>
# --- 结束日志显示 ---

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
        # --- 修改：使用默认关键字进行首次检测以填充选项 --- #
        default_keywords_for_options = ["姓名", "人员姓名"]
        header_row = next((i for i, row in source_preview.iterrows() if any((key_col in str(cell)) for cell in row.astype(str) for key_col in default_keywords_for_options)), None)
        # --- 结束修改 --- #
        if header_row is not None:
            # 重置指针，读取正确的表头行
            uploaded_source_file.seek(0)
            df_source_cols = pd.read_excel(uploaded_source_file, skiprows=header_row, nrows=0).columns.tolist()
            sample_source_fields = set(df_source_cols)
        else:
            st.warning("无法在第一个源文件中自动检测表头行以获取示例字段。")
    except Exception as e:
        st.warning(f"读取源数据示例字段时出错: {e}")

# --- 新增：关键标识列选择 ---
st.markdown("<p class='simple-subheader'>🔑 选择关键标识列</p>", unsafe_allow_html=True)
pre_selected_keys = [col for col in ["姓名", "人员姓名"] if col in sample_source_fields]
key_identifier_columns = st.multiselect(
    "选择用于匹配和查找表头的关键列名（可多选）",
    options=sample_source_fields,
    default=pre_selected_keys,
    help="这些列将用于自动检测源文件表头，并作为合并扣款表时的依据。请至少选择一项。"
)
# --- 结束新增 --- #

# --- 规则匹配设置 --- #
st.markdown("<p class='simple-subheader'>🔀 字段匹配关系设置</p>", unsafe_allow_html=True)
# 只保留一个选择框，因为源文件和规则使用相同字段名
# 使用 sample_source_fields (确保它已定义并可能是 set)
source_cols_list = sorted(list(sample_source_fields)) if sample_source_fields else []

# --- 替换为 Multiselect 并添加强制单选逻辑 --- #
# 尝试预设默认值 (如果之前有选过)
default_identity = None
if st.session_state.single_selected_identity_column and st.session_state.single_selected_identity_column in source_cols_list:
    default_identity = st.session_state.single_selected_identity_column
elif not st.session_state.single_selected_identity_column:
    # --- 修改：仅当 source_cols_list 非空时尝试设置默认值 --- #
    if source_cols_list:
        # 尝试智能默认：人员身份 > 岗位类别 > 第一个选项
        if "人员身份" in source_cols_list:
            default_identity = "人员身份"
        elif "岗位类别" in source_cols_list:
            default_identity = "岗位类别"
        elif source_cols_list: # 这一层 elif 其实可以省略，因为外层 if 已保证非空
            default_identity = source_cols_list[0]
        # 将初始默认值存入 session_state
        st.session_state.single_selected_identity_column = default_identity
    # 如果 source_cols_list 为空，则 default_identity 保持 None, session state 也为 None
    # --- 结束修改 --- #

# --- 修改：确保 default 值在 options 中 --- #
current_selection_in_state = []
if st.session_state.single_selected_identity_column and st.session_state.single_selected_identity_column in source_cols_list:
    current_selection_in_state = [st.session_state.single_selected_identity_column]
# --- 结束修改 --- #

selected_identity_list = st.multiselect(
    "选择用于匹配规则的字段名 (单选)", # 修改标签以提示单选
    options=source_cols_list,
    default=current_selection_in_state,
    key="identity_multiselect", # 添加 key
    help="选择源文件和JSON规则中都使用的那个字段名进行匹配（如 人员身份, 岗位类别）。虽为多选框，但仅第一个选项生效。"
)

# 强制单选逻辑
if len(selected_identity_list) == 0:
    if st.session_state.single_selected_identity_column is not None:
        st.session_state.single_selected_identity_column = None
        st.rerun()
elif len(selected_identity_list) == 1:
    if st.session_state.single_selected_identity_column != selected_identity_list[0]:
        st.session_state.single_selected_identity_column = selected_identity_list[0]
        st.rerun()
elif len(selected_identity_list) > 1:
    # 如果用户选了多个，只保留最后一个（最新的选择）
    last_selected = selected_identity_list[-1]
    if st.session_state.single_selected_identity_column != last_selected:
         st.session_state.single_selected_identity_column = last_selected
         st.rerun()
    # 否则，如果最后一个和 state 相同，但仍有多选，也需要强制刷新回单选
    elif len(current_selection_in_state) != 1 or current_selection_in_state[0] != last_selected:
         st.rerun()
# --- 结束替换和逻辑 --- #

# --- 结束规则匹配设置 --- #

# --- 移动：数据有效性校验区域 --- #
st.markdown("<p class='simple-subheader'>️✅ 数据有效性校验</p>", unsafe_allow_html=True)
if st.button("🔍 检查数据有效性", key="validate_data_btn"):
    validation_placeholder = st.container() # 创建容器显示结果
    with validation_placeholder:

        # --- 开始实现混合校验逻辑 --- #
        validation_errors = []
        validation_warnings = []

        # B. 检查文件是否上传 (复用侧边栏逻辑稍微修改)
        if not all(required_files_status.values()):
            validation_errors.append(f"必需文件缺失或无效: {', '.join(name for name, uploaded in required_files_status.items() if not uploaded)}")
        # 检查用户是否选择了关键列和身份列
        if not key_identifier_columns:
             validation_errors.append("请在上方'关键标识列'控件中选择至少一项。") # 修改提示
        if not selected_identity_list:
             validation_errors.append("请在上方'用于匹配规则的字段名'控件中选择一项。") # 修改提示

        # 如果基础文件或选择缺失，则不继续检查
        if validation_errors:
             # H. 显示最终校验结果 (仅错误部分)
             st.error("**校验失败:**\n" + "\n".join(validation_errors))
             if 'validation_passed' in st.session_state: del st.session_state.validation_passed # 清除旧状态

        else:
            try:
                # C. 读取所有表头信息
                # 扣款表
                actual_deduction_fields = set()
                try:
                    file_deductions.seek(0)
                    deduction_df_headers = pd.read_excel(file_deductions, header=2, nrows=0) # 只读表头
                    actual_deduction_fields = set(deduction_df_headers.columns)
                except Exception as e:
                    validation_errors.append(f"读取扣款表表头失败: {e}")

                # 模板表 (如果上传)
                actual_template_fields = []
                template_available = False
                if file_template:
                    try:
                        file_template.seek(0)
                        template_df_header = pd.read_excel(file_template, skiprows=2, nrows=1)
                        actual_template_fields = template_df_header.columns.tolist()
                        template_available = True
                    except Exception as e:
                        validation_warnings.append(f"读取模板表表头失败: {e} (目标字段有效性将无法检查)")

                # 所有源文件
                all_actual_source_fields = set()
                source_read_errors = []
                default_keywords_for_header = ["姓名", "人员姓名"]
                for i, src_file in enumerate(source_files):
                    try:
                        src_file.seek(0)
                        preview_df = pd.read_excel(src_file, header=None, nrows=20)
                        header_row_idx = next((idx for idx, row in preview_df.iterrows() if any((key in str(cell)) for cell in row.astype(str) for key in default_keywords_for_header)), None)
                        if header_row_idx is not None:
                             src_file.seek(0) # 需要重置指针以正确读取列
                             df_cols = pd.read_excel(src_file, header=header_row_idx, nrows=0).columns.tolist()
                             all_actual_source_fields.update(df_cols)
                        else:
                             source_read_errors.append(f"文件 '{src_file.name}' 未能自动检测到表头行 (使用默认关键字)。")
                    except Exception as e:
                         source_read_errors.append(f"读取源文件 '{src_file.name}' 的列名失败: {e}")
                if source_read_errors:
                     validation_warnings.extend(source_read_errors)
                if not all_actual_source_fields:
                     validation_errors.append("未能从任何源文件中成功读取列名。")

                # D. 读取 JSON 规则 (已在前面加载到 st.session_state.mapping_data)
                if 'mapping_data' not in st.session_state or not st.session_state.mapping_data:
                     validation_errors.append("无法加载 JSON 映射规则。")
                else:
                     field_mappings = st.session_state.mapping_data.get('field_mappings', [])

                     # 如果前面步骤有错误，则停止进一步检查
                     if not validation_errors:
                         # F. 执行字段重复检查
                         common_fields = all_actual_source_fields.intersection(actual_deduction_fields)
                         repeated_non_key_fields = common_fields - set(key_identifier_columns)
                         if repeated_non_key_fields:
                             validation_errors.append(f"字段冲突：以下字段同时存在于源文件和扣款表中（非关键列）: {sorted(list(repeated_non_key_fields))}。请修改列名确保唯一性。")

                         # G. 执行 JSON 规则有效性检查
                         available_fields = all_actual_source_fields.union(actual_deduction_fields)
                         invalid_source_map = []
                         invalid_target_map = []

                         # --- 新增：预收集所有定义的目标字段 --- #
                         all_defined_target_fields = set()
                         for r in field_mappings:
                             for m in r.get("mappings", []):
                                 if m.get("target_field"):
                                     all_defined_target_fields.add(m["target_field"])
                         # --- 结束新增 --- #

                         for rule_idx, rule in enumerate(field_mappings):
                             # --- 使用 Session State --- #
                             rule_id = rule.get(st.session_state.single_selected_identity_column, f"规则 #{rule_idx}")
                             # --- 结束使用 --- #
                             for map_idx, mapping in enumerate(rule.get("mappings", [])):
                                 if "source_field" in mapping: # 简单映射
                                     src = mapping["source_field"]
                                     tgt = mapping.get("target_field")
                                     if src not in available_fields:
                                         invalid_source_map.append(f"规则 '{rule_id}': 源字段 '{src}' 在源文件或扣款表中未找到。")
                                     if template_available and tgt and tgt not in actual_template_fields:
                                         invalid_target_map.append(f"规则 '{rule_id}': 目标字段 '{tgt}' (来自源 '{src}') 在模板文件中未找到。")
                                 elif "source_fields" in mapping: # 复杂映射
                                     src_list = mapping["source_fields"]
                                     tgt = mapping.get("target_field")
                                     for src in src_list:
                                         # --- 修改校验条件和警告消息 --- #
                                         if src not in available_fields and src not in all_defined_target_fields:
                                             invalid_source_map.append(f"规则 '{rule_id}' (计算): 源字段 '{src}' 在源文件/扣款表中未找到，且未被其他规则定义为目标字段。")
                                         # --- 结束修改 --- #
                                     if template_available and tgt and tgt not in actual_template_fields:
                                         invalid_target_map.append(f"规则 '{rule_id}' (计算): 目标字段 '{tgt}' 在模板文件中未找到。")

                         if invalid_source_map:
                              # --- 修改警告消息标题和格式 (使用 f-string) --- #
                              warning_list_md = "\n* ".join(invalid_source_map)
                              validation_warnings.append(f"**JSON 规则警告：部分计算所需的源字段无法直接从文件或从其他规则生成 (请检查 JSON 或文件):**\n* {warning_list_md}")
                              # --- 结束修改 --- #
                         if invalid_target_map:
                              # --- 修改错误消息标题和格式 (使用 f-string) --- #
                              error_list_md = "\n* ".join(invalid_target_map)
                              validation_errors.append(f"**JSON 规则错误：部分目标字段在模板文件中未找到:**\n* {error_list_md}")
                              # --- 结束修改 --- #

            except Exception as validation_ex:
                 validation_errors.append(f"校验过程中发生意外错误: {validation_ex}")

            # H. 显示最终校验结果 (完整版)
            if validation_errors:
                 st.error("**校验失败:**\n" + "\n".join(validation_errors))
                 st.session_state.validation_passed = False # 可选：用于后续控制
            if validation_warnings:
                 st.warning("**校验警告:**\n" + "\n".join(validation_warnings))
            # 只有没有错误时才算通过 (允许有警告)
            if not validation_errors and validation_warnings:
                 st.success("✅ 数据和规则有效性检查通过 (但存在警告)。")
                 st.session_state.validation_passed = True
            elif not validation_errors and not validation_warnings:
                 st.success("✅ 数据和规则有效性检查通过！")
                 st.session_state.validation_passed = True
            elif validation_errors: # 确保失败时状态被设置
                 if 'validation_passed' not in st.session_state or st.session_state.validation_passed is not False:
                     st.session_state.validation_passed = False

        # --- 结束实现混合校验逻辑 --- #

    validation_placeholder = st.container()
# --- 结束校验区域 --- #

# 只有当映射文件有效时才显示编辑和可视化区域
if st.session_state.get('mapping_valid') is True:
    with st.expander("📋 映射规则编辑与可视化（支持新增/校验/下载）", expanded=False):
        # 可视化字段映射统计
        field_count = {"有效映射": 0, "源字段缺失": 0, "目标字段缺失": 0} # Keep structure for now
        missing_target_details = [] # 用于存储缺失目标字段的详细信息

        # 确保 current_sample_source_fields 在这里可用
        current_sample_source_fields = sample_source_fields

        for rule in field_mappings:
            # 获取当前规则的标识符，用于日志/错误信息
            # 使用用户在 selectbox 中选择的字段名
            # --- 使用 Session State --- #
            rule_identity_value = rule.get(st.session_state.single_selected_identity_column, "未知规则标识")
            # --- 结束使用 --- #

            for mapping in rule.get("mappings", []):
                src = mapping.get("source_field", "")
                tgt = mapping.get("target_field", "")

                # 只对简单映射进行源/目标字段校验
                if "source_field" in mapping:
                    is_valid = False # 标记当前映射是否有效
                    # 如果源字段存在 (基于上面的移除，现在总是执行这个 else 逻辑，所以移除 else)
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
                         is_valid = True # is_valid 似乎没在别处用，但暂时保留
                    # (注意: 复杂映射 ("source_fields") 不在此处校验源/目标字段是否存在)

        # --- 显示缺失字段详情 --- #
        st.markdown("---") # 分隔线, 移除 impunity
        if missing_target_details:
            st.warning("**目标字段缺失详情 (与模板文件对比):**")
            for detail in missing_target_details:
                st.markdown(f"- 规则 **'{detail['rule_id']}'**: 目标字段 `'{detail['target']}'` (来自 `'{detail['source']}'`) 在模板文件中未找到。")
        # --- 结束新增表单 ---

        # 映射编辑
        for i, rule in enumerate(field_mappings):
            # --- 修改：使用 Session State --- #
            identity_value = rule.get(st.session_state.single_selected_identity_column, '未知') # 获取身份值
            bianzhi_value = rule.get('编制', '') # 保留编制
            st.markdown(f"**{st.session_state.single_selected_identity_column}: {identity_value} | 编制: {bianzhi_value}**") # 动态显示
            # --- 结束修改 --- #
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

        # 下载保存
        edited_json_for_download = json.dumps({"field_mappings": field_mappings}, ensure_ascii=False, indent=2)
        st.download_button("📥 下载当前映射规则 JSON", edited_json_for_download, file_name="字段映射规则_编辑版.json", mime="application/json")

        # 移除 impunity 并添加合适的按钮文本
        if st.button("💾 保存映射规则备份到本地"):
            save_path = "./映射规则_保存备份.json"
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(edited_json_for_download)
                st.success(f"已保存到：{save_path}")
            except Exception as save_err:
                st.error(f"保存文件时出错: {save_err}")

# --- 处理触发区域 ---
st.markdown("---") # 分隔线

# --- 新增：根据校验状态决定按钮是否可用 --- #
validation_status = st.session_state.get('validation_passed', None) # None: 未校验, False: 失败, True: 成功
disable_processing_button = (validation_status is not True)
button_tooltip = "请先点击上方的 '检查数据有效性' 按钮并通过校验。" if disable_processing_button else "开始合并处理所有上传的文件。"
# --- 结束 --- #

if st.button("🚀 开始处理数据", type="primary", disabled=disable_processing_button, help=button_tooltip):
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
    if not selected_identity_list:
        log("请选择用于匹配规则的字段名！", "ERROR")
        valid_inputs = False
    if not key_identifier_columns:
        log("请至少选择一个关键标识列名！", "ERROR")
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
                # 读取扣款表，从第三行读取表头
                deduction_df = pd.read_excel(tmp_deduct_path, header=2)
                # 记录读取到的列名和前几行数据
                log(f"读取到的扣款表列名: {deduction_df.columns.tolist()}", "INFO")
                log(f"扣款表明细 (前 5 行): \n{deduction_df.head().to_string()}", "INFO")
            finally:
                os.unlink(tmp_deduct_path)

            # 校验扣款表姓名列
            key_col_found = False
            name_columns = key_identifier_columns
            actual_name_col = None
            for key_col in name_columns:
                if key_col in deduction_df.columns:
                    key_col_found = True
                    actual_name_col = key_col # 记录找到的姓名列
                    break
            if not key_col_found:
                log(f"扣款表必须包含用户选择的关键标识列中的至少一个 ({name_columns})！", "ERROR")
                st.stop()
            else:
                log(f"扣款数据读取成功，找到关键标识列: '{actual_name_col}'。", "INFO")

            # 自动确定扣款字段列表
            all_deduction_cols = deduction_df.columns.tolist()
            selected_deduction_fields = [col for col in all_deduction_cols if col != actual_name_col]
            log(f"自动识别用于合并的扣款字段 (共 {len(selected_deduction_fields)} 个): {selected_deduction_fields}", "INFO")
            if not selected_deduction_fields:
                 log("警告：扣款表中除了姓名列外未找到其他字段。", "WARNING")

            # 在调用process_sheet之前添加预处理步骤
            print("\n=== 预处理扣款数据 ===")
            print(f"扣款数据形状: {deduction_df.shape}")
            print(f"扣款数据列: {deduction_df.columns.tolist()}")
            print(f"扣款数据前5行:\n{deduction_df.head().to_string()}")

            # 确保所有选中的扣款字段都是数值类型
            for field in selected_deduction_fields:
                if field in deduction_df.columns:
                    deduction_df[field] = pd.to_numeric(deduction_df[field], errors='coerce').fillna(0)
                    print(f"\n处理字段 {field}:")
                    print(f"数据类型: {deduction_df[field].dtype}")
                    print(f"非零值数量: {(deduction_df[field] != 0).sum()}")
                    print(f"前5个值: {deduction_df[field].head().to_list()}")

            # --- 添加日志：检查 '补发工资' 规则加载情况 ---
            bufa_rule_found = False
            # --- 新增：在检查前先获取 current_field_mappings --- #
            current_field_mappings = st.session_state.get('mapping_data', {}).get('field_mappings', [])
            # --- 结束新增 --- #
            for identity_rule in field_mappings:
                for mapping in identity_rule.get("mappings", []):
                    if mapping.get("target_field") == "补发工资":
                        # --- 使用 Session State --- #
                        log(f"DEBUG: Found rule for '补发工资' under identity '{identity_rule.get(st.session_state.single_selected_identity_column, 'N/A')}':", "DEBUG")
                        # --- 结束使用 --- #
                        log(f"  Source Fields: {mapping.get('source_fields')}", "DEBUG")
                        log(f"  Calculation: {mapping.get('calculation')}", "DEBUG")
                        bufa_rule_found = True
                        # break # 可以取消注释，如果确定每个身份规则下只有一个目标字段
                # if bufa_rule_found:
                    # break # 可以取消注释，如果只需要找到第一个匹配的规则
            if not bufa_rule_found:
                log("WARNING: No mapping rule found with target_field='补发工资' in loaded configuration.", "WARNING")
            # --- 结束添加 ---

            # --- 新增：预过滤映射规则 --- #
            log("开始预过滤映射规则...", "INFO")
            filtered_mappings_for_processing = []
            actual_deduction_fields = set(deduction_df.columns)
            # 使用之前获取的 sample_source_fields
            # 注意：sample_source_fields 可能未在所有分支初始化，需要确保它存在
            if 'sample_source_fields' not in locals():
                 # 如果 sample_source_fields 因某种原因未定义 (例如没有上传源文件，虽然前面有校验)
                 # 这里可以设置为空集合，或者记录一个错误然后停止？设置为集合可能更安全
                 log("警告：未能获取源文件样本字段用于规则过滤，将不执行过滤。", "WARNING")
                 filtered_mappings_for_processing = current_field_mappings # 不过滤
            else:
                filtered_rule_count = 0
                original_mapping_count = 0
                for rule in current_field_mappings:
                    original_mapping_count += len(rule.get("mappings", []))
                    filtered_rule = rule.copy()
                    filtered_rule["mappings"] = []
                    # --- 使用 Session State --- #
                    rule_id_for_log = rule.get(st.session_state.single_selected_identity_column, '未知规则') # 用于日志
                    # --- 结束使用 --- #

                    for mapping in rule.get("mappings", []):
                        if "source_field" in mapping:
                            src = mapping["source_field"]
                            # 条件：源字段在扣款表存在 且 在源文件样本中不存在
                            if src in actual_deduction_fields and src not in sample_source_fields:
                                log(f"  - 过滤掉规则 '{rule_id_for_log}' 中的无效映射: 源 '{src}' 仅存在于扣款表。", "DEBUG")
                                filtered_rule_count += 1
                                continue # 跳过这个映射
                            else:
                                filtered_rule["mappings"].append(mapping) # 保留有效映射
                        elif "source_fields" in mapping:
                            filtered_rule["mappings"].append(mapping) # 保留复杂映射
                        else:
                            # 如果映射格式未知，也保留？或者警告？暂时保留
                            filtered_rule["mappings"].append(mapping)

                    filtered_mappings_for_processing.append(filtered_rule)
                log(f"映射规则预过滤完成。共过滤掉 {filtered_rule_count} 个无效的简单映射。", "INFO")
            # --- 结束预过滤 --- #

            # 3. 处理每个源文件
            all_results = []
            has_error = False
            # --- 使用 Session State --- #
            identity_column_to_use = st.session_state.single_selected_identity_column
            log(f"开始逐个处理 {len(source_files)} 个源文件... (使用 '{identity_column_to_use}' 字段匹配)", "INFO")
            # --- 结束使用 --- #
            with st.spinner(f"正在处理 {len(source_files)} 个源文件..."):
                for i, uploaded_file in enumerate(source_files):
                    log(f"[{i+1}/{len(source_files)}] 处理文件: {uploaded_file.name}", "INFO")
                    tmp_source_path = None
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_source:
                            tmp_source.write(uploaded_file.getvalue())
                            tmp_source_path = tmp_source.name

                        # --- BEGIN: Add logging for source data before processing ---
                        try:
                            # Attempt to read source file to log info (need to find header)
                            preview_df_for_header = pd.read_excel(tmp_source_path, header=None, nrows=20) # Read first 20 rows to find header
                            # --- 修改：使用 key_identifier_columns --- #
                            header_row_source = next((idx for idx, row in preview_df_for_header.iterrows() if any((key_col in str(cell)) for cell in row.astype(str) for key_col in key_identifier_columns)), None)
                            # --- 结束修改 --- #

                            if header_row_source is not None:
                                df_source_preview = pd.read_excel(tmp_source_path, header=header_row_source)
                                log(f"  -> 源文件 [{uploaded_file.name}] 读取成功 (使用 {key_identifier_columns} 检测到表头行: {header_row_source + 1})，准备送入 process_sheet...", "INFO") # 修改日志
                                log(f"     源文件列名: {df_source_preview.columns.tolist()}", "INFO")
                                log(f"     源文件数据 (前 5 行):\\n{df_source_preview.head().to_string()}", "INFO")
                            else:
                                log(f"  -> 警告: 未能在源文件 [{uploaded_file.name}] 前 20 行找到 {key_identifier_columns} 中的任何一个作为表头，无法记录源数据详情。", "WARNING") # 修改日志
                                # Optionally, proceed without preview logging or stop? For now, just warn.
                        except Exception as read_err:
                             log(f"  -> 警告: 尝试读取源文件 [{uploaded_file.name}] 进行日志记录时出错: {read_err}", "WARNING")
                        # --- END: Add logging for source data before processing ---

                        # --- BEGIN: Add simulated merge for diagnostics ---
                        if 'df_source_preview' in locals() and header_row_source is not None: # Ensure preview was read
                            try:
                                # --- 修改：使用 key_identifier_columns 和 actual_name_col --- #
                                source_key_to_use = None
                                if actual_name_col in df_source_preview.columns: # 优先使用扣款表找到的那个
                                    source_key_to_use = actual_name_col
                                else: # 否则查找第一个在源表中的用户选择的关键列
                                     source_key_to_use = next((col for col in key_identifier_columns if col in df_source_preview.columns), None)

                                if source_key_to_use and actual_name_col: # 确保两边都有可用的键
                                    log(f"  -> 执行模拟合并 (源: {uploaded_file.name}, 扣款表) on: 源='{source_key_to_use}', 扣款='{actual_name_col}'...", "INFO") # 修改日志
                                    simulated_merge = pd.merge(df_source_preview, deduction_df, left_on=source_key_to_use, right_on=actual_name_col, how='left', suffixes=('', '_扣款')) # 使用 left_on/right_on
                                    log(f"     模拟合并结果列名: {simulated_merge.columns.tolist()}", "INFO")
                                    log(f"     模拟合并结果数据 (前 5 行):\\n{simulated_merge.head().to_string()}", "INFO")
                                else:
                                    log(f"  -> 警告: 无法执行模拟合并，源文件({key_identifier_columns})或扣款表({actual_name_col})缺少有效的公共或指定关键列。", "WARNING") # 修改日志
                                # --- 结束修改 --- #
                            except Exception as merge_err:
                                log(f"  -> 错误: 执行模拟合并时出错: {merge_err}", "ERROR")
                        else:
                             log(f"  -> 跳过模拟合并，因为未能成功读取源文件预览。", "INFO")
                        # --- END: Add simulated merge for diagnostics ---

                        # 添加调用 process_sheet 的日志
                        log(f"  -> 调用核心处理函数 process_sheet...", "INFO")
                        result_df = process_sheet(
                            tmp_source_path,
                            deduction_df,
                            filtered_mappings_for_processing,
                            selected_deduction_fields,
                            # --- 使用 Session State --- #
                            identity_column_to_use,
                            identity_column_to_use # NOTE: Passing identity key twice? Check process_sheet definition if intended.
                            # --- 结束使用 --- #
                         )
                        log(f"  <- process_sheet 返回，结果行数: {len(result_df) if result_df is not None else 'None'}", "INFO")

                        # --- BEGIN: Add logging for result data after processing ---
                        if result_df is not None and not result_df.empty:
                             log(f"     process_sheet 返回 [{uploaded_file.name}] 列名: {result_df.columns.tolist()}", "INFO")
                             log(f"     process_sheet 返回 [{uploaded_file.name}] 数据 (前 5 行):\\n{result_df.head().to_string()}", "INFO")
                             all_results.append(result_df)
                             log(f"[{i+1}/{len(source_files)}] 文件 {uploaded_file.name} 处理成功。", "SUCCESS")
                        # --- END: Add logging for result data after processing ---
                        else:
                             # Keep original warning log if result is None or empty
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

                        # 在合并操作后添加日志
                        log(f"合并后的DataFrame列名: {combined_df.columns.tolist()}", "INFO")
                        log(f"合并后的DataFrame数据 (前 5 行):\n{combined_df.head().to_string()}", "INFO")

                        # 在扣款明细计算前添加日志
                        log(f"用于计算的扣款明细字段: {selected_deduction_fields}", "INFO")
                        log(f"扣款明细字段的值 (前 5 行):\n{combined_df[selected_deduction_fields].head().to_string()}", "INFO")

                        # 在扣款明细计算后添加日志
                        # --- 修改：移除硬编码访问 --- #
                        total_deduction_col_name = '扣发合计'
                        if total_deduction_col_name in combined_df.columns:
                            log(f"计算后的'{total_deduction_col_name}'和其他扣款明细字段的值 (前 5 行):\n{combined_df[[total_deduction_col_name] + selected_deduction_fields].head().to_string()}", "INFO")
                        else:
                            log(f"计算后的扣款明细字段的值 (未找到'{total_deduction_col_name}'列) (前 5 行):\n{combined_df[selected_deduction_fields].head().to_string()}", "INFO")
                        # --- 结束修改 --- #

                        # 在最终输出前添加日志
                        log(f"最终输出的DataFrame列名: {combined_df.columns.tolist()}", "INFO")
                        log(f"最终输出的DataFrame数据 (前 5 行):\n{combined_df.head().to_string()}", "INFO")

                        # 验证结果
                        print("\n=== 验证处理结果 ===")
                        print(f"结果数据形状: {result_df.shape}")
                        print(f"结果数据列: {result_df.columns.tolist()}")

                        # 检查扣款字段
                        for field in selected_deduction_fields:
                            if field in result_df.columns:
                                print(f"\n检查字段 {field}:")
                                print(f"数据类型: {result_df[field].dtype}")
                                print(f"非零值数量: {(result_df[field] != 0).sum()}")
                                print(f"前5个值: {result_df[field].head().to_list()}")
                            else:
                                print(f"\n警告: 字段 {field} 不在结果数据中")

                        # 检查姓名列的匹配情况
                        # --- 修改：使用 key_identifier_columns --- #
                        common_key_for_validation = None
                        for key_col in key_identifier_columns:
                            if key_col in result_df.columns and key_col in deduction_df.columns:
                                common_key_for_validation = key_col
                                break

                        if common_key_for_validation:
                            print(f"\n=== 使用关键列 '{common_key_for_validation}' 检查姓名匹配情况 ===")
                            source_names = set(result_df[common_key_for_validation].dropna().unique())
                            deduction_names = set(deduction_df[common_key_for_validation].dropna().unique())
                            matched_names = source_names.intersection(deduction_names)
                            print(f"源文件中的 '{common_key_for_validation}' 数量: {len(source_names)}")
                            print(f"扣款表中的 '{common_key_for_validation}' 数量: {len(deduction_names)}")
                            print(f"成功匹配的 '{common_key_for_validation}' 数量: {len(matched_names)}")
                            if len(matched_names) < len(source_names):
                                print(f"警告: 部分源文件中的 '{common_key_for_validation}' 未能匹配到扣款数据")
                                print("未匹配示例:")
                                unmatched = source_names - matched_names
                                print(list(unmatched)[:5])
                        else:
                            print(f"\n警告: 未能在结果表和扣款表中找到共同的关键标识列 ({key_identifier_columns}) 用于匹配验证。")
                        # --- 结束修改 --- #

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
