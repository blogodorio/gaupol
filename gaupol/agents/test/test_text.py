# Copyright (C) 2005-2008 Osmo Salomaa
#
# This file is part of Gaupol.
#
# Gaupol is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Gaupol is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Gaupol. If not, see <http://www.gnu.org/licenses/>.

import gaupol
import gtk


class TestSpellCheckAgent(gaupol.TestCase):

    def setup_method(self, method):

        self.application = self.new_application()
        respond = lambda *args: gtk.RESPONSE_DELETE_EVENT
        self.application.flash_dialog = respond
        gaupol.SpellCheckDialog.flash_dialog = respond

    def test_on_check_spelling_activate(self):

        respond = lambda *args: gtk.RESPONSE_OK
        gaupol.SpellCheckDialog.flash_dialog = respond
        gaupol.conf.spell_check.language = "en"
        self.application.get_action("check_spelling").activate()
        gaupol.conf.spell_check.language = "wo"
        self.application.get_action("check_spelling").activate()
        del gaupol.SpellCheckDialog.flash_dialog

    def test_on_configure_spell_check_activate(self):

        self.application.get_action("configure_spell_check").activate()

    def test_on_correct_texts_activate(self):

        real_show = gaupol.TextAssistant.show
        gaupol.TextAssistant.show = lambda *args: None
        self.application.get_action("correct_texts").activate()
        gaupol.TextAssistant.show = real_show
