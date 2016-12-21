=========
 EECS GS
=========

Tools for grading and submitting (creating coming soon) gradescripted programming assignments for the UTK EECS department.

------------
 Components
------------

    grader.py
        A tool that automates grading a collection of assignment submissions. Compatible with ``submit.py`` as well as the department submit script submissions.

    submit.py
        A tool for submitting assignments. The ``submit.cfg.json.example`` is an example of how to write a config for the script. The intention is that a student facing submit script will be written which invokes ``submit.py`` with an appropriate config for the course.

----------
 Examples
----------

Running the grader for a simple lab case:

::

    $> python grader.py --due="09/03/2016 06:00" \
                        --labpath="/home/bvz/cs140/Labs/Lab1" \
                        --sourcefiles="moonglow.cpp,checkerboard.cpp" \
                        --compcmds="g++ -o moonglow moonglow.cpp, g++ -o checkerboard checkerboard.cpp"

Submitting the current directory using the raw submit script:

::

    $> python submit.py submit.config.json.example
