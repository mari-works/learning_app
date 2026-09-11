import pytest
import re
import io
from datetime import datetime, timedelta
from uuid import uuid4

from learning_app.app import (
    User,
    app as flask_app,
    build_flashcard_replay_url,
    build_practice_replay_label,
    build_practice_replay_url,
    build_quiz_question,
    load_quiz_questions,
    pause_quiz_state,
    parse_keyword_upload,
    parse_question_upload,
    resume_quiz_state,
    select_initial_curriculum_items,
)
from learning_app.models import (
    connect_db,
    create_course,
    delete_course,
    ensure_default_course,
    get_keyword,
    get_keywords,
    get_material_counts,
    get_material_title,
    get_course,
    get_exam_settings,
    init_db,
    list_courses,
    query_db,
    replace_material_data,
    update_material_data,
    update_exam_settings,
    set_learning_status,
)
from werkzeug.datastructures import FileStorage


@pytest.fixture
def client():
    with flask_app.test_client() as client:
        yield client


def extract_csrf(response):
    text = response.get_data(as_text=True)
    marker = 'name="csrf_token" value="'
    start = text.index(marker) + len(marker)
    end = text.index('"', start)
    return text[start:end]


def register(client, username=None, password="password123"):
    username = username or f"pytest_user_{uuid4().hex}"
    response = client.get("/register")
    token = extract_csrf(response)
    return client.post(
        "/register",
        data={
            "csrf_token": token,
            "username": username,
            "password": password,
            "password_confirm": password,
        },
        follow_redirects=True,
    )


def login(client, username, password="password123", follow_redirects=True):
    response = client.get("/login")
    token = extract_csrf(response)
    return client.post(
        "/login",
        data={
            "csrf_token": token,
            "username": username,
            "password": password,
        },
        follow_redirects=follow_redirects,
    )


def logout(client):
    response = client.get("/")
    token = extract_csrf(response)
    return client.post("/logout", data={"csrf_token": token}, follow_redirects=False)


def get_user_id(username):
    with flask_app.app_context():
        return User.query.filter_by(username=username).one().id


def test_guest_login_is_temporary_and_cleans_learning_data(client):
    login_page = client.get("/login")
    token = extract_csrf(login_page)
    response = client.post(
        "/guest-login",
        data={"csrf_token": token},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "ゲスト" in response.get_data(as_text=True)
    assert "履歴は保存されません" in response.get_data(as_text=True)

    with client.session_transaction() as guest_session:
        guest_user_id = int(guest_session["_user_id"])
        assert guest_session["is_guest"] is True

    with connect_db(flask_app.config["DATABASE"]) as sqlite_db:
        sqlite_db.execute(
            """
            INSERT INTO history (session_type, result, created_at, user_id)
            VALUES ('term', '理解済み', ?, ?)
            """,
            (datetime.now().isoformat(), guest_user_id),
        )
        sqlite_db.commit()

    response = logout(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    assert query_db(
        flask_app.config["DATABASE"],
        "SELECT id FROM history WHERE user_id = ?",
        (guest_user_id,),
    ) == []
    with flask_app.app_context():
        assert flask_app.extensions["sqlalchemy"].session.get(User, guest_user_id) is None


def first_keyword_ids(limit=2):
    rows = query_db(
        flask_app.config["DATABASE"],
        "SELECT id FROM keywords ORDER BY id LIMIT ?",
        (limit,),
    )
    return [row["id"] for row in rows]


def latest_history_for_user(user_id, session_type):
    return query_db(
        flask_app.config["DATABASE"],
        """
        SELECT *
        FROM history
        WHERE user_id = ? AND session_type = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id, session_type),
        one=True,
    )


def test_home(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    register_response = register(client)
    assert register_response.status_code == 200

    response = client.get("/")
    assert response.status_code == 200


def test_home_review_starts_random_ten_item_sets(client):
    register(client, username=f"pytest_home_review_{uuid4().hex}")

    term_response = client.get("/review/terms/start")
    assert term_response.status_code == 302
    assert "/flashcards?" in term_response.headers["Location"]
    assert "learning_mode=review" in term_response.headers["Location"]
    term_ids = re.search(r"keyword_ids=([^&]+)", term_response.headers["Location"]).group(1).replace("%2C", ",").split(",")
    assert 1 <= len(term_ids) <= 10

    question_response = client.get("/review/questions/start")
    assert question_response.status_code == 302
    assert "/practice/quiz?" in question_response.headers["Location"]
    assert "mode=review" in question_response.headers["Location"]
    question_ids = re.search(r"question_ids=([^&]+)", question_response.headers["Location"]).group(1).replace("%2C", ",").split(",")
    assert 1 <= len(question_ids) <= 10

    quiz_response = client.get(question_response.headers["Location"])
    assert quiz_response.status_code == 200
    with client.session_transaction() as quiz_session:
        assert len(quiz_session["quiz"]["question_ids"]) == len(question_ids)
        assert quiz_session["quiz"]["learning_mode"] == "review"


def test_about(client):
    register(client, username=f"pytest_about_user_{uuid4().hex}")
    response = client.get("/about")
    assert response.status_code == 200


def test_load_quiz_questions_reads_csv():
    questions = load_quiz_questions()
    assert questions
    assert questions[0]["question"]


def csv_upload(name, content):
    return FileStorage(stream=io.BytesIO(content.encode("utf-8-sig")), filename=name)


def test_material_csv_parsers_validate_and_normalize_rows():
    terms = parse_keyword_upload(csv_upload(
        "terms.csv",
        "ID,カテゴリ,用語,意味\n1,基礎,hello,こんにちは\n",
    ))
    questions = parse_question_upload(csv_upload(
        "questions.csv",
        "ID,カテゴリ,問題,正答,誤答1,誤答2,誤答3,解説\n1,基礎,helloの意味は？,こんにちは,こんばんは,さようなら,ありがとう,基本の挨拶\n",
    ))

    assert terms[0]["keyword"] == "hello"
    assert terms[0]["item_no"] == "1"
    assert terms[0]["category"] == "基礎"
    assert terms[0]["learning_order"] is None
    assert questions[0]["incorrect_answers"] == ["こんばんは", "さようなら", "ありがとう"]
    assert questions[0]["learning_order"] is None


def test_initial_curriculum_selection_distributes_up_to_three_categories():
    items = [
        {"id": 1, "item_no": "1", "category": "A"},
        {"id": 2, "item_no": "4", "category": "A"},
        {"id": 3, "item_no": "2", "category": "B"},
        {"id": 4, "item_no": "3", "category": "C"},
        {"id": 5, "item_no": "5", "category": "D"},
    ]

    selected = select_initial_curriculum_items(items, limit=4)

    assert [item["id"] for item in selected] == [1, 3, 4, 2]
    assert {item["category"] for item in selected} == {"A", "B", "C"}


def test_replace_material_data_uses_validated_rows(tmp_path):
    db_path = tmp_path / "material.db"
    init_db(db_path)
    replace_material_data(
        db_path,
        "英語基礎",
        [{
            "big_category": "語学", "category": "基礎", "item_no": "1",
            "item_name": "挨拶", "keyword": "hello", "meaning": "こんにちは",
        }],
        [{
            "id": 1, "category": "基礎", "question": "helloの意味は？",
            "correct_answer": "こんにちは",
            "incorrect_answers": ["こんばんは", "さようなら", "ありがとう"],
            "explanation": "基本の挨拶",
        }],
    )

    assert get_material_title(db_path) == "英語基礎"
    assert get_material_counts(db_path) == {"keywords": 1, "questions": 1}

    update_material_data(db_path, "英語入門")
    assert get_material_title(db_path) == "英語入門"
    assert get_material_counts(db_path) == {"keywords": 1, "questions": 1}


def test_course_registry_keeps_material_databases_separate(tmp_path):
    registry_path = tmp_path / "registry.db"
    second_course_path = tmp_path / "second.db"
    init_db(registry_path)
    ensure_default_course(registry_path)
    init_db(second_course_path)
    update_material_data(second_course_path, "英語教材")
    create_course(registry_path, "english", "英語教材", second_course_path)

    courses = list_courses(registry_path)
    assert {course["id"] for course in courses} == {"default", "english"}
    assert get_course(registry_path, "english")["database_path"] == str(second_course_path.resolve())
    assert get_material_title(second_course_path) == "英語教材"
    assert get_exam_settings(second_course_path)["enabled"] is False

    update_exam_settings(second_course_path, True, 20, 30)
    assert get_exam_settings(second_course_path) == {
        "enabled": True,
        "questions": 20,
        "minutes": 30,
    }

    delete_course(registry_path, "english")
    assert get_course(registry_path, "english") is None


def test_build_quiz_question_shuffles_choices_and_keeps_answer():
    question = build_quiz_question(load_quiz_questions()[0])
    assert len(question["choices"]) == 4
    assert question["correct_answer"] in [choice["text"] for choice in question["choices"]]


def test_login_logout_and_invalid_login_message(client):
    username = f"pytest_auth_{uuid4().hex}"
    register_response = register(client, username=username)
    assert register_response.status_code == 200

    logout_response = logout(client)
    assert logout_response.status_code == 302
    assert "/login" in logout_response.headers["Location"]

    bad_response = login(client, username, password="wrong-password")
    assert "ユーザー名またはパスワードが正しくありません" in bad_response.get_data(as_text=True)

    good_response = login(client, username)
    assert good_response.status_code == 200
    assert client.get("/").status_code == 200


def test_flashcard_resume_api_saves_and_clears_for_logged_in_user(client):
    keyword_ids = first_keyword_ids(2)
    if len(keyword_ids) < 2:
        pytest.skip("keyword fixtures are not available")

    username = f"pytest_flash_resume_{uuid4().hex}"
    register(client, username=username)
    user_id = get_user_id(username)

    response = client.post(
        "/api/flashcard_resume",
        json={
            "index": 1,
            "direction": "term_to_meaning",
            "card_ids": keyword_ids,
            "learning_mode": "category",
            "learning_category": "テストカテゴリ",
            "range_label": "テスト範囲",
        },
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    saved = query_db(
        flask_app.config["DATABASE"],
        "SELECT * FROM flashcard_resume WHERE user_id = ?",
        (user_id,),
        one=True,
    )
    assert saved is not None
    assert saved["current_index"] == 1
    assert saved["learning_mode"] == "category"
    assert saved["learning_category"] == "テストカテゴリ"

    clear_response = client.post("/api/flashcard_resume/clear", json={})
    assert clear_response.status_code == 200
    assert clear_response.get_json()["success"] is True
    cleared = query_db(
        flask_app.config["DATABASE"],
        "SELECT * FROM flashcard_resume WHERE user_id = ?",
        (user_id,),
        one=True,
    )
    assert cleared is None


def test_record_study_time_saves_user_scoped_learning_mode(client):
    username = f"pytest_study_time_{uuid4().hex}"
    register(client, username=username)
    user_id = get_user_id(username)

    response = client.post(
        "/api/record_study_time",
        json={
            "session_type": "term",
            "duration_seconds": 75,
            "learning_mode": "category",
            "learning_category": "機械学習",
        },
    )
    assert response.status_code == 200
    assert response.get_json()["recorded"] is True

    history = latest_history_for_user(user_id, "term")
    assert history is not None
    assert history["duration_seconds"] == 75
    assert history["learning_type"] == "vocabulary"
    assert history["learning_mode"] == "category"
    assert history["learning_category"] == "機械学習"


def test_keyword_list_uses_user_progress_status(client):
    keyword_ids = first_keyword_ids(1)
    if not keyword_ids:
        pytest.skip("keyword fixtures are not available")

    username = f"pytest_keyword_progress_{uuid4().hex}"
    register(client, username=username)
    user_id = get_user_id(username)

    set_learning_status(
        flask_app.config["DATABASE"],
        keyword_ids[0],
        "理解済み",
        user_id=user_id,
    )

    keywords = get_keywords(flask_app.config["DATABASE"], user_id=user_id)
    listed_keyword = next(item for item in keywords if item["id"] == keyword_ids[0])
    detailed_keyword = get_keyword(flask_app.config["DATABASE"], keyword_ids[0], user_id=user_id)

    assert listed_keyword["learning_status"] == "理解済み"
    assert detailed_keyword["learning_status"] == "理解済み"


def test_practice_answer_records_history_and_repeat_url(client):
    username = f"pytest_practice_{uuid4().hex}"
    register(client, username=username)
    user_id = get_user_id(username)

    response = client.get("/practice/quiz?mode=random&limit=1&reset=1&start=1")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    token = extract_csrf(response)
    question_id = re.search(r'name="question_id" value="([^"]+)"', html).group(1)
    choice = re.search(r'name="choice" value="([^"]+)"', html).group(1)

    result_response = client.post(
        "/practice/quiz",
        data={
            "csrf_token": token,
            "action": "finish",
            "mode": "random",
            "limit": "1",
            "question_id": question_id,
            "choice": choice,
        },
        follow_redirects=True,
    )
    assert result_response.status_code == 200
    assert "もう一度解く" in result_response.get_data(as_text=True)

    history = latest_history_for_user(user_id, "practice")
    assert history is not None
    assert history["item_id"] == int(question_id)
    assert history["learning_type"] == "question"
    assert history["learning_mode"] == "random"


def test_exam_pause_resume_keeps_elapsed_time():
    start_time = (datetime.utcnow() - timedelta(seconds=420)).isoformat()
    state = {
        "mode": "exam",
        "start_time": start_time,
        "started_at": start_time,
        "elapsed_seconds": 0,
    }

    paused = pause_quiz_state(state.copy(), graded=False)
    assert paused["paused"] is True
    assert paused["paused_elapsed_seconds"] >= 400

    resumed = resume_quiz_state(paused)
    assert "paused" not in resumed
    assert resumed["elapsed_seconds"] >= 400
    assert resumed["start_time_ms"]


def test_daily_recommendations_are_fixed_for_the_day(client):
    username = f"pytest_daily_{uuid4().hex}"
    register(client, username=username)
    user_id = get_user_id(username)

    client.get("/")
    term_key = f"daily_term_recommendation:{user_id}"
    practice_key = f"daily_practice_recommendation:{user_id}"
    with client.session_transaction() as sess:
        first_term_ids = list(sess[term_key]["keyword_ids"])
        first_question_ids = list(sess[practice_key]["question_ids"])
        assert sess[term_key]["is_initial_learning"] is True
        assert sess[term_key]["reason"] == "IDの小さい未学習用語から選びました"
        assert sess[practice_key]["has_enough_history"] is False
        assert sess[practice_key]["reason"] == "IDの小さい問題を、最大3カテゴリから選びました。"

    selected_terms = [get_keyword(flask_app.config["DATABASE"], term_id, user_id=user_id) for term_id in first_term_ids]
    assert all(term["learning_status"] == "未学習" for term in selected_terms)
    assert len({term["category"] for term in selected_terms}) <= 3
    question_map = {question["id"]: question for question in load_quiz_questions()}
    assert len({question_map[question_id]["category"] for question_id in first_question_ids}) <= 3

    client.get("/")
    with client.session_transaction() as sess:
        assert sess[term_key]["keyword_ids"] == first_term_ids
        assert sess[practice_key]["question_ids"] == first_question_ids
        assert len(sess[term_key]["keyword_ids"]) == 10
        assert len(sess[practice_key]["question_ids"]) == 10


def test_replay_url_helpers_preserve_fixed_ids():
    with flask_app.test_request_context("/"):
        flashcard_url = build_flashcard_replay_url(
            keyword_ids=[3, 1],
            direction="term_to_meaning",
            limit=10,
            learning_mode="daily_recommendation",
        )
        practice_state = {
            "mode": "random",
            "question_limit": 10,
            "learning_mode": "daily_recommendation",
            "fixed_question_ids": [5, 2, 9],
        }
        practice_url = build_practice_replay_url(practice_state)

    assert "keyword_ids=3,1" in flashcard_url
    assert "learning_mode=daily_recommendation" in flashcard_url
    assert "question_ids=5,2,9" in practice_url
    assert build_practice_replay_label(practice_state) == "もう一度本日のおすすめを解く"
