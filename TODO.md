Apoorva: build_road/build_settlement bug in player.py needs fixing
build_mode toggle from the Build button and on_mouse_motion hover detection

Tristin: implement node_to_pixel in frontend.py 
make hoverable circles


Amanda: MERGE VIEWS INTO MAIN. add setup phase flag and connect the placement validation to the actual Player objects. Make road and settlement placement helper functions so that it can be used in both setup and catan views without duplicating all of the code (need help from Tristin) Make helper functions for building board and hover logic for placing settlements and roads to make SetupView not an entire copy of the CatanView
