TOON Differ (ToonDiff) API
================================

The :mod:`toonverter.analysis.diff` module provides comprehensive tools for comparing two data structures. ...

.. automodule:: toonverter.analysis.diff
   :members:
   :exclude-members: ToonDiffer, ToonDiffResult

.. autoclass:: toonverter.analysis.diff.ToonDiffResult
   :members:
   :undoc-members:
   :no-index:
   :exclude-members: summary, visualize, __init__

   .. automethod:: toonverter.analysis.diff.ToonDiffResult.__init__
      :no-index:
   .. automethod:: toonverter.analysis.diff.ToonDiffResult.summary
   .. automethod:: toonverter.analysis.diff.ToonDiffResult.visualize

.. autoclass:: toonverter.analysis.diff.ToonDiffer
   :members:
   :undoc-members:
   :no-index:
   :exclude-members: _compare_structures, diff_data, diff_files, __init__

   .. automethod:: toonverter.analysis.diff.ToonDiffer.__init__
      :no-index:
   .. automethod:: toonverter.analysis.diff.ToonDiffer.diff_data
   .. automethod:: toonverter.analysis.diff.ToonDiffer.diff_files