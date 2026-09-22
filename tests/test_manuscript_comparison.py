"""Guard against silent corruption in the manuscript's reading comparison."""
import shutil
import unittest

from scripts.update_manuscript_diff import reading_text


@unittest.skipUnless(shutil.which('detex'), 'detex is required for manuscript extraction')
class ManuscriptComparisonTests(unittest.TestCase):
    def test_many_distinct_formulas_survive_extraction(self):
        formulas = [f'$x_{{{i}}}+y$' for i in range(25)]
        self.assertEqual(reading_text(' '.join(formulas)), ' '.join(formulas))

    def test_nested_table_layout_does_not_leak_or_remove_cells(self):
        source = r'''\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}p{3cm}r}
\multicolumn{2}{@{}l}{Training signals}\\
LaDiM & 50/50\\
\end{tabular*}'''
        self.assertEqual(reading_text(source), 'Training signals LaDiM & 50/50')

    def test_bibliography_macros_are_excluded_but_entries_remain(self):
        source = r'''\begin{thebibliography}{2}
\providecommand{\url}[1]{#1}
\bibitem[Author(2026)]{author2026} Author. A research paper. 2026.
\end{thebibliography}'''
        self.assertEqual(reading_text(source), 'Author. A research paper. 2026.')


if __name__ == '__main__':
    unittest.main()
