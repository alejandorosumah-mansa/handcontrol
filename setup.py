"""
Setup script for Minority Report (HandControl)
"""
from setuptools import setup, find_packages

setup(
    name='minority-report',
    version='2.0.0',
    description='Gesture-based cursor control — Minority Report edition',
    author='HandControl Team',
    python_requires='>=3.8',
    packages=find_packages(),
    install_requires=[
        'opencv-python>=4.8.0',
        'mediapipe>=0.10.8',
        'pyautogui>=0.9.50',
        'pyyaml>=5.1',
        'numpy>=1.19.0',
        'Pillow>=9.0',
    ],
    entry_points={
        'console_scripts': [
            'minority-report=main:main',
        ],
    },
)
