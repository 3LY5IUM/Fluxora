# src/credits.py
import streamlit as st

def render_credits_ui(names=None, title="Credits"):
    """
    Render a simple Credits tab that lists contributor names.
    Call this inside a tab/container in app.py.
    """
    names = names or [
        "Hardik Sahu",
        "Akshat Lad",
        "Krrish Agrawal",
        "Archit Sapra",
    ]

    st.header(title)
    st.markdown("This app was built by: Team Code&Chil")  # st.markdown renders formatted text [8]
    for n in names:
        st.markdown(f"- {n}")  # simple Markdown bullet list [8]

    # Optional project notes
    st.markdown("---")  # horizontal rule [8]
    st.markdown("Thank you for using this application.")  # basic Markdown text [8]

