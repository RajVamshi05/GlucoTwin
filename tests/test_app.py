from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]

def test_all_pages_and_controls():
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30).run()
    assert not app.exception
    for page in ['Patient Profile','Live Digital Twin','Risk and Explainability','Scenario Simulator','Model Performance','Prediction Log']:
        app.sidebar.radio[0].set_value(page).run();assert not app.exception, str(app.exception)
        if page=='Live Digital Twin':
            before=app.session_state['twins'][app.sidebar.selectbox[0].value].cursor
            app.button(key='step').click().run();assert not app.exception
            assert app.session_state['twins'][app.sidebar.selectbox[0].value].cursor==before+1
        if page=='Scenario Simulator':
            for scenario in ['Meal annotation now','Recent activity','Missing sensor interval','Alternate historical profile']:
                next(w for w in app.selectbox if w.label=='Scenario').set_value(scenario).run();assert not app.exception
    app.sidebar.selectbox[0].select('PT-0002').run();assert not app.exception
