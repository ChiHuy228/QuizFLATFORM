from django.urls import path

from . import views


urlpatterns = [

    # ==================================================
    # TRANG CHỦ
    # ==================================================

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "quiz/review/",
        views.quiz_review,
        name="quiz_review"
    ),

    # ==================================================
    # TRANG SAU KHI TẠO QUIZ
    # ==================================================

    path(
        "quiz/<uuid:share_code>/created/",
        views.quiz_created,
        name="quiz_created"
    ),

    # ==================================================
    # TRANG LÀM BÀI
    # ==================================================

    path(
        "quiz/<uuid:share_code>/",
        views.take_quiz,
        name="take_quiz"
    ),

    # ==================================================
    # NỘP BÀI
    # ==================================================

    path(
        "quiz/<uuid:share_code>/submit/",
        views.submit_quiz,
        name="submit_quiz"
    ),

    # ==================================================
    # KẾT QUẢ
    # ==================================================

    path(
        "quiz/<uuid:share_code>/result/<int:attempt_id>/",
        views.result,
        name="result"
    ),

]
