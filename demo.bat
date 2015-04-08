@echo off

echo RUNNING RED
main.py red --directory testset

echo RUNNING GREEN
main.py green --directory testset

echo RUNNING BLUE
main.py blue --directory testset --mode color

echo RUNNING YELLOW
main.py yellow --directory testset --mode color