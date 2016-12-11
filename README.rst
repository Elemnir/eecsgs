=========
 EECS GS
=========

A tool for grading (creating and submitting coming soon) gradescripted programming assignments for the UTK EECS department.

------------
 Components
------------

    grader.py
        A library of functions that automate grading a collection of assignment submissions.

    submit.py
        (WIP) A tool for creating and submitting assignments. The `config.json.example` is an example of how to write a config for the script. The intention is that student facing submit scripts will be written which invoke `submit.py` with an appropriate config for the course.

----------
 Examples
----------

Running the grader for a simple lab case:

::

    $> python grader.py --due="09/03/2016 06:00" \
                        --labpath="/home/bvz/cs140/Labs/Lab1" \
                        --sourcefiles="moonglow.cpp,checkerboard.cpp" \
                        --compcmds="g++ -o moonglow moonglow.cpp, g++ -o checkerboard checkerboard.cpp"
