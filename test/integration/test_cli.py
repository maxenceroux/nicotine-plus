# COPYRIGHT (C) 2021 Nicotine+ Team
#
# GNU GENERAL PUBLIC LICENSE
#    Version 3, 29 June 2007
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
import unittest


class CLITest(unittest.TestCase):

    def test_cli(self):
        """ Verify that CLI-exclusive functionality works """

        output = subprocess.check_output(["python3", "-m", "pynicotine", "--help"], timeout=1)
        self.assertTrue(str(output).find("--help") > -1)

        output = subprocess.check_output(["python3", "-m", "pynicotine", "--version"], timeout=1)
        self.assertTrue(str(output).find("Nicotine+") > -1)
