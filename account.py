# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Andrea Gallina (<a.gallina@cgsoftware>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
import time


class vat_registry(orm.Model):

    _name = 'vat.registry'
    _description = 'Definizione Registri iva italiani'
    _columns = {
        'reg_vat_code': fields.char('Codice Registro', size=10),
        'name': fields.char('Descrizione', size=30),
        'activity_code': fields.char('Codice Attivita', size=10),
        'journal_ids': fields.one2many('vat.registry.journals', 'Lista Sezionali'),
        'type': fields.selection(
                (('Vendite', 'vendite'), ('Acquisti', 'acquisti'), ('Corrispettivi', 'corrispettivi')),
                'Tipo Registro'),
    }


    class vat_registry_journals(orm.Model):

        _name = 'vat.registry.journals'
        _description = 'Lista dei sezionali del registro iva'
        _columns = {
            'vat_registry_id': fields.many2one('vat.registry', 'Registro Iva'),
            'journal_id': fields.many2one('account.journal', 'Sezionale'),
        }
