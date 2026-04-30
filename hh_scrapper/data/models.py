from django.db import models

class UniqueUser(models.Model):
    tg_id = models.BigIntegerField(
        verbose_name="Telegram ID",
        unique=True,
        null=False,
        blank=False
    )
    username = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"


class Skill(models.Model):
    name = models.CharField(
        verbose_name="Название навыка", blank=False, null=False, max_length=255
    )

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"

class Profession(models.Model):
    name = models.CharField(
        verbose_name="Название профессии / запрос",
        max_length=255
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Профессия / Запрос"
        verbose_name_plural = "Профессии / Запросы"

class UserProfessionRequest(models.Model):
    """
    Промежуточная модель — связь "многие ко многим" с дополнительной информацией
    """
    user = models.ForeignKey(
        UniqueUser,
        on_delete=models.CASCADE,
        related_name='requests',
        verbose_name="Пользователь"
    )
    
    profession = models.ForeignKey(
        Profession,
        on_delete=models.CASCADE,
        related_name='user_requests',
        verbose_name="Запрос"
    )

    class Meta:
        verbose_name = "Запрос пользователя"
        verbose_name_plural = "Запросы пользователей"
        unique_together = ('user', 'profession')

class Area(models.Model):
    hh_id = models.IntegerField(unique=True, verbose_name="ID на HH.ru")
    name = models.CharField(max_length=255, verbose_name="Название")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    
    class Meta:
        verbose_name = "Регион"
        verbose_name_plural = "Регионы"
    
    def __str__(self):
        return self.name        

class Vacancy(models.Model):
    name = models.CharField(max_length=500, verbose_name="Название вакансии")
    url = models.URLField(max_length=500, verbose_name="Ссылка на HH.ru")
    
    published_at = models.DateField(verbose_name="Дата публикации")
    salary = models.PositiveIntegerField(null=True, blank=True, verbose_name="Зарплата")
    
    areas = models.ManyToManyField(
        'Area', 
        related_name='vacancies',
        verbose_name="Регионы"
    )
    
    profession = models.ForeignKey(
        'Profession', 
        on_delete=models.CASCADE, 
        related_name='vacancies'
    )
    
    user_request = models.ForeignKey(
        'UserProfessionRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacancies'
    )
    
    skills = models.ManyToManyField('Skill', related_name='vacancies')
    
    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
        ordering = ['-published_at']

    def __str__(self):
        return self.name

