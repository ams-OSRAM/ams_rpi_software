Stats Engine Usage
===========================================


The stats_engine `stats.py <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/characterization_ams/stats_engine/stats.py?treeId=refs%2Fheads%2Fmaster>`_ 
is the lowest level of the **ams Characterization** module. Functions either take an image or stack of images and compute basic pixel metrics.
The easiest way to get all component wise metrics is 
`stats.agg_result() <file:///C:/workspace/characterization/docs/build/html/stats_engine.html#characterization_ams.stats_engine.stats.agg_results>`_.

Take the following case where we have a stack of images with dim (num_images, rows, cols) like the one shown below:

.. image:: /_static/images/single_exp.png
   :align: center

|
We pass the stack of  images corresponding to a single operating point to
`stats.agg_result() <file:///C:/workspace/characterization/docs/build/html/stats_engine.html#characterization_ams.stats_engine.stats.agg_results>`_.

.. code-block:: python

    results = stats.agg_result(image_stack)

And the resulting output:

.. image:: /_static/images/c1.png
   :align: center

|
Each metric can be obtained individually, but for most use cases getting all metrics of interest is the easiest approach.
A list and example usage for all 
`stats.py <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/characterization_ams/stats_engine/stats.py?treeId=refs%2Fheads%2Fmaster>`_
can be found in `Test_Stats.html <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/notebooks/stats_engine/Test_Stats.html?treeId=refs%2Fheads%2Fmaster>`_.