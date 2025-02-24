from django.core.management.base import BaseCommand
from learning.models import Track, Dot, SubDot, Assessment
import random

class Command(BaseCommand):
    help = 'Populates the database with sample Python learning tracks'

    def handle(self, *args, **kwargs):
        # Python Basics Track
        python_basics = Track.objects.create(
            title="Python Fundamentals",
            description="Master the basics of Python programming language. Learn variables, data types, control structures, and more."
        )

        # Variables and Data Types Dot
        variables_dot = Dot.objects.create(
            track=python_basics,
            title="Variables and Data Types",
            order=1
        )

        # Variables Introduction SubDot
        SubDot.objects.create(
            dot=variables_dot,
            title="Introduction to Variables",
            content="""Variables are containers for storing data values. In Python, you don't need to declare variables with specific types; Python automatically determines the type based on the value assigned.

A variable is created the moment you first assign a value to it. Python uses = to assign values to variables.""",
            code_snippet='''# Variable assignment examples
name = "John"
age = 25
height = 1.75
is_student = True

print(f"Name: {name}")
print(f"Age: {age}")
print(f"Height: {height}")
print(f"Is Student: {is_student}")''',
            image_url="https://www.pythonforbeginners.com/wp-content/uploads/2021/03/Python-Variables-1024x512.png",
            order=1
        )

        # Numbers SubDot
        SubDot.objects.create(
            dot=variables_dot,
            title="Numbers in Python",
            content="""Python supports several types of numbers:
- Integers (int): Whole numbers, positive or negative
- Floating-point numbers (float): Decimal numbers
- Complex numbers: Numbers with real and imaginary parts""",
            code_snippet='''# Number types in Python
integer_num = 42
float_num = 3.14
complex_num = 2 + 3j

print(f"Integer: {integer_num}, Type: {type(integer_num)}")
print(f"Float: {float_num}, Type: {type(float_num)}")
print(f"Complex: {complex_num}, Type: {type(complex_num)}")''',
            image_url="https://pythonguides.com/wp-content/uploads/2020/09/Python-number-1.png",
            order=2
        )

        # Control Flow Dot
        control_flow_dot = Dot.objects.create(
            track=python_basics,
            title="Control Flow",
            order=2
        )

        # If Statements SubDot
        SubDot.objects.create(
            dot=control_flow_dot,
            title="If Statements",
            content="""Control flow statements determine the order in which program code executes. The if statement is one of the most commonly used control flow statements.

An if statement can be followed by an optional elif (else if) statement and else statement.""",
            code_snippet='''# If statement example
age = 18

if age < 13:
    print("You're a child")
elif age < 20:
    print("You're a teenager")
else:
    print("You're an adult")''',
            image_url="https://pythonbasics.org/wp-content/uploads/2019/02/if-else.png",
            order=1
        )

        # Advanced Python Track
        advanced_python = Track.objects.create(
            title="Advanced Python Concepts",
            description="Dive deep into advanced Python concepts including decorators, generators, and object-oriented programming."
        )

        # OOP Dot
        oop_dot = Dot.objects.create(
            track=advanced_python,
            title="Object-Oriented Programming",
            order=1
        )

        # Classes SubDot
        SubDot.objects.create(
            dot=oop_dot,
            title="Classes and Objects",
            content="""Object-Oriented Programming (OOP) is a programming paradigm that provides a means of structuring programs so that properties and behaviors are bundled into individual objects.

A class is a blueprint for creating objects. Objects are instances of a class.""",
            code_snippet='''# Class definition example
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def bark(self):
        return f"{self.name} says Woof!"

# Creating objects
my_dog = Dog("Rex", 3)
print(my_dog.bark())''',
            image_url="https://www.programiz.com/sites/tutorial2program/files/python-class-and-object.png",
            order=1
        )

        # Create assessments for each dot
        assessment_questions = [
            ("What is a variable in Python?", "A variable is a container for storing data values."),
            ("What are the main number types in Python?", "The main number types in Python are integers (int), floating-point numbers (float), and complex numbers."),
            ("Explain if statements in Python.", "If statements are used for conditional execution of code based on boolean conditions."),
            ("What is Object-Oriented Programming?", "OOP is a programming paradigm that uses objects containing data and code to structure programs."),
            ("How do you create a class in Python?", "A class is created using the 'class' keyword followed by the class name."),
        ]

        for dot in [variables_dot, control_flow_dot, oop_dot]:
            for _ in range(5):  # Create 5 assessments per dot
                question, answer = random.choice(assessment_questions)
                Assessment.objects.create(
                    dot=dot,
                    question=question,
                    answer=answer
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with Python tracks'))
