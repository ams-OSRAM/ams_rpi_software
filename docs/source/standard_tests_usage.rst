Standard Tests Usage
===========================================


`standard_tests <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/tree/characterization_ams/standard_tests?treeId=refs%2Fheads%2Fmaster>`_ 
are built upon the stats_engine `stats.py <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/characterization_ams/stats_engine/stats.py?treeId=refs%2Fheads%2Fmaster>`_ 
and the `emva <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/characterization_ams/emva/emva.py?treeId=refs%2Fheads%2Fmaster>`_.
This module allows for more control over how the calculations are done and can handle multiple operating points at once. 

PTC
------------------------------------------------------------------------

`ptc <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/characterization_ams/standard_tests/ptc.py?treeId=refs%2Fheads%2Fmaster>`_ can be
used much like the stats engine but with multipe operating points, or can handle an exposure sweep which provides every metric calculated in
`emva 4.0 <https://www.emva.org/wp-content/uploads/EMVA1288Linear_4.0Release.pdf>`_.

Take the following case:

.. image:: /_static/images/exp_sweep.png
   :align: center

Here each image stack in the list corresponds to some unique operating point. For `ptc <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/characterization_ams/standard_tests/ptc.py?treeId=refs%2Fheads%2Fmaster>`_
this must be an exposure sweep, but for `ptc.get_stats() <file:///C:/workspace/characterization/docs/build/html/standard_tests.html#characterization_ams.standard_tests.ptc.get_stats>`_ this can be any unique operating point.
The doc string for `ptc.get_stats() <file:///C:/workspace/characterization/docs/build/html/standard_tests.html#characterization_ams.standard_tests.ptc.get_stats>`_ is shown below:

~~~ python
def get_stats(images,
              df=pd.DataFrame(),
              rmv_ttn=False,
              hpf=True,
              rmv_black=True,
              temp_imgs=None,
              L=None):
    """
    calculate all statistics per EMVA 4.0 definition

    Keyword Arguments:
        images (list): list of images where each element is array
                       with dim (num_images, width, height)
        df (pd.DataFrame): DataFrame of parameters associated with each image
                           in image stack, right now it is assumed DataFrame
                           index corresponds to indx of images
        rmv_ttn (bool): if True subtract off residual temporal noise
        hpf (bool): if true high pass filter image prior to spatial variance calc
        rmv_black (bool): if True creates black level subtracted columns + originals
        temp_images (list|None): If 'images' is a list of frame averages then total
                                 temporal variance images must be passed here
        L (int|None): If average frames are passed to 'images' original stack size
                      must be passed.  
    Returns:
        data (pd.DataFrame): DataFrame of all statistics with updated
                             column names and a column with black level
                             subtracted for each metric
    """
~~~
    
And the resulting output:

.. image:: /_static/images/c1.png
   :align: center

|
Each metric can be obtained individually, but for most use cases getting all metrics of interest is the easiest approach.
A list and example usage for all 
`stats.py <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/characterization_ams/stats_engine/stats.py?treeId=refs%2Fheads%2Fmaster>`_
can be found in `Test_Stats.html <https://forge.ams.com/ctf/code/projects.jupy/git/scm.characterization/file/notebooks/stats_engine/Test_Stats.html?treeId=refs%2Fheads%2Fmaster>`_.