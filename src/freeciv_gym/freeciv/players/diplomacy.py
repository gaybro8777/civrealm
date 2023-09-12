# Copyright (C) 2023  The Freeciv-gym project
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


import gymnasium

from freeciv_gym.freeciv.connectivity.civ_connection import CivConnection
from freeciv_gym.freeciv.connectivity.client_state import ClientState
from freeciv_gym.freeciv.game.ruleset import RulesetCtrl

from freeciv_gym.freeciv.utils.base_controller import CivPropController
from freeciv_gym.freeciv.utils.base_state import DictState
from freeciv_gym.freeciv.utils.base_action import NoActions

import freeciv_gym.freeciv.players.player_const as player_const
from freeciv_gym.freeciv.utils.freeciv_logging import fc_logger
from freeciv_gym.freeciv.players.player_const import CONFLICTING_CLAUSES


class DiplomacyState(DictState):
    def __init__(self, diplomatic_state: dict):
        super().__init__()
        self.diplomatic_state = diplomatic_state

    def _update_state(self, pplayer):
        self._state = {player_id: {'diplomatic_state': diplomatic_state}
                       for player_id, diplomatic_state in self.diplomatic_state.items()}

    def get_observation_space(self):
        diplomatic_space = gymnasium.spaces.Dict({
            'diplomatic_state': gymnasium.spaces.Discrete(player_const.DS_LAST)
        })
        return gymnasium.spaces.Dict({player_id: diplomatic_space for player_id in self.diplomatic_state.keys()})


class DiplomacyCtrl(CivPropController):
    def __init__(self, ws_client: CivConnection, clstate: ClientState, rule_ctrl: RulesetCtrl, dipl_evaluator=None):
        super().__init__(ws_client)
        self.diplstates = dict()
        self.others_diplstates = dict()
        self.reason_to_cancel = dict()
        self.contact_turns_left = dict()
        self.diplomacy_request_queue = []
        self.diplomacy_clause_map = {}
        self.active_diplomacy_meeting_id = None
        self.rule_ctrl = rule_ctrl
        self.clstate = clstate
        self.prop_state = DiplomacyState(self.diplstates)
        self.prop_actions = NoActions(ws_client)
        # TODO: dipl_evaluator is not implemented yet
        self.dipl_evaluator = dipl_evaluator

    def register_all_handlers(self):
        self.register_handler(59, "handle_player_diplstate")
        self.register_handler(96, "handle_diplomacy_init_meeting")
        self.register_handler(98, "handle_diplomacy_cancel_meeting")
        self.register_handler(100, "handle_diplomacy_create_clause")
        self.register_handler(102, "handle_diplomacy_remove_clause")
        self.register_handler(104, "handle_diplomacy_accept_treaty")

    # Check whether the given nation is barbarian or pirate.
    def is_barbarian_pirate(self, nation_id):
        return self.rule_ctrl.nations[nation_id]['rule_name'].lower() in ['barbarian', 'pirate']

    def is_republic_democracy(self, gov_id):
        return self.rule_ctrl.governments[gov_id]['rule_name'] in ['Republic', 'Democracy']

    """
    for counterpart in self.players:
            if counterpart == cur_player:
                state.update(self.dipl_ctrl.get_current_state(counterpart))

        state["shared_vision"] = 0

        if (pplayer['diplstates'] !== undefined) {
            pplayer['diplstates'].forEach(function (st, i) {
              if (st['state'] !== DS_NO_CONTACT && i !== pplayer['playerno']) {
                var dplst = intel_data['dipl'][st['state']]
                if (dplst === undefined) {
                  dplst = {
                    state: get_diplstate_text(st['state']),
                    nations: []
                  }
                  intel_data['dipl'][st['state']] = dplst
                }
                dplst['nations'].append(nations[players[i]['nation']]['adjective'])
              }
            })
          }

        if self.clstate.can_client_control():
            if not self.player_is_myself(player_id) and diplstates[player_id] != None:
                state["dipl_state"] = get_diplstate_text(diplstates[player_id])

            if pplayer['gives_shared_vision'].isSet(cur_player['playerno']):
                state["shared_vision"] += 1 # "To you"
            if cur_player['gives_shared_vision'].isSet(player_id):
                state["shared_vision"] += 2 # "To Them
    """

    def handle_player_diplstate(self, packet):

        if packet['plr1'] not in self.reason_to_cancel:
            self.reason_to_cancel[packet['plr1']] = dict()
        self.reason_to_cancel[packet['plr1']][packet['plr2']] = packet['has_reason_to_cancel']

        if packet['plr1'] not in self.contact_turns_left:
            self.contact_turns_left[packet['plr1']] = dict()
        self.contact_turns_left[packet['plr1']][packet['plr2']] = packet['contact_turns_left']

        if packet['plr1'] not in self.others_diplstates:
            self.others_diplstates[packet['plr1']] = dict()
        self.others_diplstates[packet['plr1']][packet['plr2']] = packet['type']

        cur_playerno = self.clstate.player_num()
        if packet['plr1'] == cur_playerno:
            opposite_player = 'plr2'
        elif packet['plr2'] == cur_playerno:
            opposite_player = 'plr1'
        else:
            return

        self.diplstates[packet[opposite_player]] = packet['type']

        """
        if packet['type'] == DS_WAR and self.check_not_dipl_states(packet[opposite_player]):
            self.dipl_evaluator.alert_war(packet[opposite_player])
        """
        """
        // TODO: remove current diplstates (after moving all users to the new one),
        //       or just make it a reference to players[me].diplstates
        //
        // There's no need to set players[packet.plr2].diplstates, as there'll be
        // a packet for that.  In fact, there's a packet for each of (p1,x) and (p2,x)
        // when the state changes between p1 and p2, and for all pairs of players
        // when a turn begins
        """
        """
        player1 = self.player_ctrl.players[packet['plr1']]
        if not "diplstates" in player1.keys():
            player1["diplstates"] = [{} for _ in self.player_ctrl.players]

        player1["diplstates"][packet['plr2']] = {
                            "state": packet['type'],
                            "turns_left": packet['turns_left'],
                            "contact_turns_left": packet['contact_turns_left']
                            }
        """

    def handle_diplomacy_init_meeting(self, packet):
        if packet['counterpart'] not in self.diplomacy_request_queue:
            self.diplomacy_request_queue.append(packet['counterpart'])

        self.diplomacy_clause_map[packet['counterpart']] = []
        fc_logger.debug(f'diplomacy_clause_map: {self.diplomacy_clause_map}')
        self.refresh_diplomacy_request_queue()

    def handle_diplomacy_cancel_meeting(self, packet):
        counterpart = packet['counterpart']

        if counterpart in self.diplomacy_request_queue:
            del self.diplomacy_request_queue[self.diplomacy_request_queue.index(counterpart)]
        # setTimeout(refresh_diplomacy_request_queue, 1000)

        if self.active_diplomacy_meeting_id == counterpart:
            self.refresh_diplomacy_request_queue()

        if counterpart in self.diplomacy_clause_map:
            del self.diplomacy_clause_map[counterpart]
        fc_logger.debug(f'diplomacy_clause_map: {self.diplomacy_clause_map}')

    def refresh_diplomacy_request_queue(self):
        if self.diplomacy_request_queue:
            next_meeting = self.diplomacy_request_queue[0]
            if next_meeting is not None:
                self.active_diplomacy_meeting_id = next_meeting
        else:
            self.active_diplomacy_meeting_id = None

    def handle_diplomacy_create_clause(self, packet):

        if packet not in self.diplomacy_clause_map[packet['counterpart']]:
            if packet['type'] in CONFLICTING_CLAUSES:
                for clause_id, clause in enumerate(self.diplomacy_clause_map[packet['counterpart']]):
                    if clause['type'] == packet['type']:
                        self.diplomacy_clause_map[packet['counterpart']][clause_id] = packet
                        fc_logger.debug(f'diplomacy_clause_map: {self.diplomacy_clause_map}')
                        return

            self.diplomacy_clause_map[packet['counterpart']].append(packet)
        fc_logger.debug(f'diplomacy_clause_map: {self.diplomacy_clause_map}')

    def handle_diplomacy_remove_clause(self, packet):
        clause_list = self.diplomacy_clause_map[packet['counterpart']]
        for i, check_clause in enumerate(clause_list):
            if (packet['giver'] == check_clause['giver'] and
                    packet['type'] == check_clause['type'] and
                    packet['value'] == check_clause['value']):
                del self.diplomacy_clause_map[packet['counterpart']][i]
                fc_logger.debug(f'diplomacy_clause_map: {self.diplomacy_clause_map}')
                break

    def handle_diplomacy_accept_treaty(self, packet):
        counterpart = packet['counterpart']
        myself_accepted = packet['I_accepted']
        other_accepted = packet['other_accepted']

        if myself_accepted and other_accepted:
            if counterpart in self.diplomacy_request_queue:
                del self.diplomacy_request_queue[self.diplomacy_request_queue.index(counterpart)]

            if self.active_diplomacy_meeting_id == counterpart:
                self.refresh_diplomacy_request_queue()

            if counterpart in self.diplomacy_clause_map:
                del self.diplomacy_clause_map[counterpart]
            fc_logger.debug(f'diplomacy_clause_map: {self.diplomacy_clause_map}')

        '''
        if not self.active_diplomacy_meeting_id == counterpart and myself_accepted and other_accepted:
            if counterpart in self.diplomacy_request_queue:
                del self.diplomacy_request_queue[self.diplomacy_request_queue.index(counterpart)]
            elif self.active_diplomacy_meeting_id == counterpart:
                if self.dipl_evaluator is not None:
                    self.dipl_evaluator.evaluate_clauses(self.diplomacy_clause_map[counterpart], counterpart,
                                                         myself_accepted, other_accepted)
        '''

        # self.refresh_diplomacy_request_queue()
        # setTimeout(refresh_diplomacy_request_queue, 1000)

    def check_not_dipl_states(self, player_id, check_list=None):
        if check_list is None:
            check_list = [player_const.DS_WAR, player_const.DS_NO_CONTACT]
        if player_id in self.diplstates:
            if self.diplstates[player_id] not in check_list:
                return True

        return False

    def check_in_dipl_states(self, player_id, check_list=None):
        if check_list is None:
            check_list = [player_const.DS_ALLIANCE, player_const.DS_TEAM]

        if player_id in self.diplstates:
            if self.diplstates[player_id] in check_list:
                return True
        else:
            return False

    @staticmethod
    def get_diplstate_text(state_id):
        if player_const.DS_ARMISTICE == state_id:
            return "Armistice"
        elif player_const.DS_WAR == state_id:
            return "War"
        elif player_const.DS_CEASEFIRE == state_id:
            return "Ceasefire"
        elif player_const.DS_PEACE == state_id:
            return "Peace"
        elif player_const.DS_ALLIANCE == state_id:
            return "Alliance"
        elif player_const.DS_NO_CONTACT == state_id:
            return "No contact"
        elif player_const.DS_TEAM == state_id:
            return "Team"
        else:
            return "Unknown state"

    """
    def evaluate_clauses(self):
        def eval_clause(counterpart, giver, ctype, value):
            pass
        if self.active_diplomacy_meeting_id != None:
            clauses = self.diplomacy_clause_map[self.active_diplomacy_meeting_id]
            for cid, clause in enumerate(clauses):
                eval_clause(clause["counterpart"], clause["giver"],
                            clause["type"], clause["value"])

    def meeting_gold_change_req(self, giver, gold):
        #Request update of gold clause
        clauses = self.diplomacy_clause_map[self.active_diplomacy_meeting_id]
        if clauses != None:
            for cid, clause in enumerate(clauses):
                if clause['giver'] == giver and clause['type'] == CLAUSE_GOLD:
                    if clause['value'] == gold:
                        return
                    self.remove_clause_req(cid)

        if gold != 0:
            packet = {"pid" : packet_diplomacy_create_clause_req,
                      "counterpart" : self.active_diplomacy_meeting_id,
                      "giver" : giver,
                      "type" : CLAUSE_GOLD,
                      "value" : gold}
            self.ws_client.send_request(packet)
    """
