import streamlit as st

def page1():
    st.write("Page 1")

def page2():
    st.write("Page 2")

pg = st.navigation({
    "Main": [st.Page(page1, title="Home")],
    "Dashboard": [
        st.Page(page2, title="Zeit & Liga"),
        st.Page(page2, title="Karten")
    ]
})
pg.run()
