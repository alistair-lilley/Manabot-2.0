""" Rules object """
from src.globals import simplify


class Rules:
    
    def __init__(self, rules_file):
        self.ruletree = self._make_rules_tree(rules_file)
    
    def _make_rules_tree(self, rules_file):
        rules_tree = RTree("root","")
        rule_lines = self._read_in_rules(rules_file)
        for rule in rule_lines:
            rulenum = rule.split(' ', 1)[0]
            rules_tree.insert(simplify(rulenum), rule)
        return rules_tree

    def _read_in_rules(self, rules_file):
        parsed_lines = []
        curr_rule = ""
        rflines = [line for line in open(rules_file)]
        for line in rflines:
            if not line.strip():
                if curr_rule:
                    parsed_lines.append(curr_rule)
                    curr_rule = ""
            else:
                curr_rule += line + " "
        return parsed_lines

    def retrieve_rule(self, rulekw):
        return self.ruletree.search_for_rule(simplify(rulekw))


class RTree:
    """
        RTree is a "rules tree". It is a tree structure for storing rules. It is
        implemented as a prefix tree, in which each node is composed of the last
        character of its "key" and its matching "value". For example, rule 100.1a
        will be found at node a under 1 -> 0 -> 0 -> 1 (omitting punct) -> a, and
        it will contain the text for the rule (including the rule number at the
        beginning). Keywords are stored under the same root node in a similar
        fashion.
    """
    def __init__(self, rulenum, rule):
        self.key = rulenum
        self.value = rule
        self.children = dict()

    def insert(self, rulenum, rule):
        if not rulenum:
            self.value = rule
        elif rulenum[0] in self.children:
            self.children[rulenum[0]].insert(rulenum[1:], rule)
        else:
            if len(rulenum) == 1:
                self.children[rulenum[0]] = RTree(rulenum[0], rule)
            else:
                self.children[rulenum[0]] = RTree(rulenum[0], "")
                self.children[rulenum[0]].insert(rulenum[1:], rule)

    def search_for_rule(self, rulenum):
        if rulenum[0] in self.children:
            if len(rulenum) == 1:
                return self.children[rulenum[0]].get_rule()
            return self.children[rulenum[0]].search_for_rule(rulenum[1:])
        return "Rule not found"

    def get_rule(self):
        return self.value + self.get_next_level()

    def get_next_level(self):
        children_values = ""
        for child in self.children:
            if not self.children[child].value:
                children_values += self.children[child].get_next_level()
            else:
                children_values += '\n' + self.children[child].value
        return children_values
