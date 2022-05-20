import re, string

class Rules:
    
    def __init__(self, rulesFile):
        self.ruletree = self._makeRulesTree(rulesFile)
    
    def _makeRulesTree(self, rulesFile):
        rulesTree = RTree("root","")
        ruleLines = self._readInRules(rulesFile)
        for rule in ruleLines:
            rulenum = rule.split(' ', 1)[0]
            rulesTree.insert(self._simplify(rulenum), rule)
        return rulesTree

    def _readInRules(self, rulesFile):
        parsedLines = []
        currRule = ""
        rflines = [line for line in open(rulesFile)]
        for line in rflines:
            if not line.strip():
                if currRule:
                    parsedLines.append(currRule)
                    currRule = ""
            else:
                currRule += line + " "
        return parsedLines

    def retrieveRule(self, rulekw):
        return self.ruletree.searchForRule(self._simplify(rulekw))

    def _simplify(self, rulenum):
        rulenum = re.sub(r'[\W\s]', '', rulenum).lower()
        return ''.join([ch for ch in rulenum if ch not in string.punctuation])


class RTree:

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

    def searchForRule(self, rulenum):
        if rulenum[0] in self.children:
            if len(rulenum) == 1:
                return self.children[rulenum[0]].getRule()
            return self.children[rulenum[0]].searchForRule(rulenum[1:])
        return "Rule not found"

    def getRule(self):
        return self.value + self.getNextLevel()

    def getNextLevel(self):
        childrenValues = ""
        for child in self.children:
            if not self.children[child].value:
                childrenValues += self.children[child].getNextLevel()
            else:
                childrenValues += '\n' + self.children[child].value
        return childrenValues
