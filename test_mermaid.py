import streamlit as st
from streamlit_markdown import st_markdown # Import the component using the correct library name

st.set_page_config(page_title="Mermaid Test")
st.title("Minimal Mermaid Rendering Test")

st.markdown("Below should be a simple flowchart:")

# Optional: Remove the basic markdown test
# st.write("--- DEBUG: Attempting to render simple Markdown ---")
# st.markdown("**This should be bold text.**")
# st.write("--- DEBUG: Finished attempting simple Markdown ---")

simple_mermaid_code = """
```mermaid
graph TD;
    A[Client] --> B(Streamlit App);
    B --> C{Renders Mermaid?};
    C -- Yes --> D[Great!];
    C -- No --> E[Hmm...];
```
"""
# Use the new component instead of st.markdown
st.write("--- DEBUG: Attempting to render simple graph using st_markdown ---")
st_markdown(simple_mermaid_code)
st.write("--- DEBUG: Finished attempting simple graph using st_markdown ---")

st.markdown("---")
st.markdown(f"Using Streamlit version: **{st.__version__}**") # 显示版本确认