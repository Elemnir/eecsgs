=========
 EECS GS
=========

A tool for grading (creating and submitting coming soon) gradescripted programming assignments for the UTK EECS department.

------------
 Components
------------

    grader.py
        A library of functions that automate grading a collection of assignment submissions.

----------
 Examples
----------

Running the grader for a simple lab case:

::

    $> python grader.py --due="09/03/2016 06:00" \
                        --labpath="/home/bvz/cs140/Labs/Lab1" \
                        --sourcefiles="moonglow.cpp,checkerboard.cpp" \
                        --compcmds="g++ -o moonglow moonglow.cpp, g++ -o checkerboard checkerboard.cpp"
