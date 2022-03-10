from types import SimpleNamespace
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Quiz
from questions.models import Question, Choice
from submissions.models import Submission, Response


@login_required
def quiz(request):
    """ Redirect user from /quiz/ to their profile """
    return redirect(reverse("profile"))


@login_required
def take_quiz(request, pk):
    user = get_object_or_404(User, username=request.user)
    # check if non-mentor trying to take quiz again, and redirect if so
    if user.profile.mentor_type == "is_not_mentor" and user.profile.taken_quiz:
        messages.success(request, "You have already submitted your responses.")
        return redirect(reverse("profile"))

    # user is mentor and can take the quiz again
    get_quiz = Quiz.objects.filter(
        name=user.profile.mentor_type).values_list("id", flat=True)[:1]
    for quiz_id in get_quiz:
        if quiz_id != pk:
            # user trying to brute-force to another quiz URL
            return redirect(take_quiz, quiz_id)
        else:
            # user accessing correct quiz URL
            quiz = Quiz.objects.get(pk=pk)
            questions = []
            for question in quiz.get_questions():
                choices = []
                for choice in question.get_choices():
                    choices.append(choice.choice)
                questions.append({
                    "id": question.pk,
                    "type": question.type,
                    "question": str(question),
                    "choices": choices,
                })

    template = "quizzes/quiz.html"
    context = {
        "quiz": quiz,
        "questions": questions,
    }

    return render(request, template, context)


@login_required
def submit_quiz_results(request, pk):
    if request.method == "POST":

        quiz = Quiz.objects.get(pk=pk)
        user = request.user
        results = []
        correct_answer = None
        is_correct = "False"
        total_correct = 0

        # convert POST results into dictionary of lists
        data = dict(request.POST.lists())
        # remove CSRF token
        data.pop("csrfmiddlewaretoken")
        questions = []
        duration = 0
        time_taken = 0

        for key, value in data.items():
            # ignore "duration" for obtaining each question
            if key == "duration":
                duration = "".join(value)
            elif key.startswith("time_taken-"):
                time_taken = "".join(value)
            elif key.startswith("q"):
                # build questions list with user's responses
                key = key.replace("q", "")
                current_question = Question.objects.get(pk=key)
                questions.append({
                    "id": key,
                    "question": current_question,
                    "user_answer": value,
                    "time_taken": time_taken
                })

        for question in questions:
            # https://docs.python.org/3/library/types.html#types.SimpleNamespace
            # SimpleNamespace allows the use of dot-notation
            q = SimpleNamespace(**question)
            question_choices = Choice.objects.filter(question=q.question)
            choices = []  # resets with each loop intentionally
            # loop through the DB question's possible choices
            for choice in question_choices:
                # if the choice is marked 'correct_answer', append to choices
                if choice.correct_answer:
                    choices.append(choice.choice)
            correct_answer = sorted(choices)  # set the correct_answer
            # check if the user's answer is equal to the correct choices
            if sorted(q.user_answer) == sorted(choices):
                is_correct = "True"
                total_correct += 1
            elif quiz.name == "is_not_mentor":
                # handle 'is_not_mentor' as always True
                is_correct = "True"
                total_correct += 1
            else:
                is_correct = "False"
            # build a dict with the user's answers + the correct answers
            results.append({
                "id": q.id,
                "question": q.question.question,
                "is_correct": is_correct,
                "correct_answer": correct_answer,
                "user_answers": q.user_answer,
                "time_taken": q.time_taken,
            })

        # calculate percentage of questions answered correctly
        questions_answered = len(questions)
        percent_correct = round((total_correct / questions_answered) * 100)

        # create new instance of Submission
        submission = Submission.objects.create(
            user=user,
            quiz=quiz,
            duration=duration,
            original_response=results,
            percent_correct=percent_correct
        )

        # create individual instances of Response for the Submission
        for result in results:
            Response.objects.create(
                submission=submission,
                question=Question.objects.get(pk=result["id"]),
                is_correct=result["is_correct"],
                correct_answer=result["correct_answer"],
                user_answer=result["user_answers"],
                time_taken=result["time_taken"],
            )

        # update the user's profile to show they've taken the quiz
        user_profile = get_object_or_404(User, username=request.user)
        user_profile.profile.taken_quiz = True
        user_profile.save()

        messages.success(request, "Your responses have been submitted!")
        return redirect(reverse("profile"))

    else:
        return redirect(take_quiz, pk)
