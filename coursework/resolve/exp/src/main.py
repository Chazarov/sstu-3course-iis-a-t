# main.py
from experta import *

class TestFact(Fact):
    pass

class TestEngine(KnowledgeEngine):
    @Rule(TestFact(value=1))
    def test_rule(self):
        print("the system is running successfully")

if __name__ == "__main__":
    engine = TestEngine()
    engine.reset()
    engine.declare(TestFact(value=1))
    engine.run()