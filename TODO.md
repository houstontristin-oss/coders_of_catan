# Group Todo Organizer

Apoorva:

* work on setup phase placement logic (resource addition for second settlement?)
* consider moving placement functionality to player class from catan_view

Tristin:

* implement node_to_pixel in frontend.py
* make hoverable circles
* fix port placement

Amanda:

* MERGE VIEWS INTO MAIN.
* add setup phase flag and connect the placement validation to the actual Player objects.
* Make road and settlement placement helper functions so that it can be used in both setup and catan views without duplicating all of the code (need help from Tristin)
* Make helper functions for building board and hover logic for placing settlements and roads to make SetupView not an entire copy of the CatanView

Nick:

* make it so only valid road placements will highlight when hovered
* do the above thing for settlement placement as well
