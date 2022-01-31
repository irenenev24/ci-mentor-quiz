import random
from django.db import models


class Quiz(models.Model):
    # quiz types available
    QUIZ_TYPE = [
        ("current_mentor", "Quiz for Mentors"),
        ("potential_mentor", "Quiz for Potential Mentors"),
    ]
    name = models.CharField(choices=QUIZ_TYPE, max_length=20)
    max_count = models.IntegerField(null=True)

    def __str__(self):
        return str(self.name)

    def get_questions(self):
        if self.pk != 2:
            # shuffle quiz unless it's potential_mentor_quiz
            questions = list(self.question_set.all())
            random.shuffle(questions)
            return questions[:self.max_count]
        else:
            return self.question_set.all()[:self.max_count]

    class Meta:
        verbose_name_plural = "Quizzes"
