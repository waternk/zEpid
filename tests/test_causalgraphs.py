import pytest

from zepid.causal.causalgraph import DirectedAcyclicGraph


@pytest.fixture
def arrow_list_1():
    return (('X', 'Y'), ('Z', 'X'), ('Z', 'Y'),
            ('W', 'X'), ('W', 'V'), ('V', 'Y'))


@pytest.fixture
def arrow_list_2():
    return (('X', 'Y'), ('X', 'C'),
            ('Y', 'C'))


@pytest.fixture
def arrow_list_3():
    return (('X', 'Y'),
            ('Y', 'V'))


@pytest.fixture
def arrow_mbias():
    return (('X', 'Y'),
            ('U1', 'X'), ('U1', 'B'),
            ('U2', 'B'), ('U2', 'Y'),
            )


@pytest.fixture
def arrow_butterfly():
    return (('X', 'Y'),
            ('B', 'X'), ('B', 'Y'),
            ('U1', 'X'), ('U1', 'B'),
            ('U2', 'B'), ('U2', 'Y'))


class TestDirectedAcyclicGraph:

    def test_adjustment_set_1(self, arrow_list_1):
        correct_set = [{"W", "Z"}, {"V", "Z"}, {"W", "V", "Z"}]

        dag = DirectedAcyclicGraph(exposure='X', outcome="Y")
        dag.add_arrows(arrow_list_1)
        dag.calculate_adjustment_sets()

        # Making sure number of adjustment sets are equal to correct sets
        assert len(dag.adjustment_sets) == len(correct_set)

        # Checking no 'double' sets in adjustment sets
        assert len(dag.adjustment_sets) == len(set(dag.adjustment_sets))

        # Checking that all adjustment sets are in the correct
        for i in dag.adjustment_sets:
            assert set(i) in list(correct_set)

    def test_min_adjustment_set_1(self, arrow_list_1):
        correct_set = [{"W", "Z"}, {"V", "Z"}]

        dag = DirectedAcyclicGraph(exposure='X', outcome="Y")
        dag.add_arrows(arrow_list_1)
        dag.calculate_adjustment_sets()

        # Making sure number of adjustment sets are equal to correct sets
        assert len(dag.minimal_adjustment_sets) == len(correct_set)

        # Checking no 'double' sets in adjustment sets
        assert len(dag.minimal_adjustment_sets) == len(set(dag.minimal_adjustment_sets))

        # Checking that all adjustment sets are in the correct
        for i in dag.minimal_adjustment_sets:
            assert set(i) in list(correct_set)

    def test_adjustment_set_2(self, arrow_list_2):
        correct_set = [()]

        dag = DirectedAcyclicGraph(exposure='X', outcome="Y")
        dag.add_arrows(arrow_list_2)
        dag.calculate_adjustment_sets()
        print(dag.adjustment_sets)

        # Making sure number of adjustment sets are equal to correct sets
        assert len(dag.adjustment_sets) == len(correct_set)

        # Checking no 'double' sets in adjustment sets
        assert len(dag.adjustment_sets) == len(set(dag.adjustment_sets))

        # Checking that minimal is the same
        assert dag.adjustment_sets == dag.minimal_adjustment_sets

    def test_adjustment_set_3(self, arrow_list_3):
        correct_set = [()]

        dag = DirectedAcyclicGraph(exposure='X', outcome="Y")
        dag.add_arrows(arrow_list_3)
        dag.calculate_adjustment_sets()
        print(dag.adjustment_sets)

        # Making sure number of adjustment sets are equal to correct sets
        assert len(dag.adjustment_sets) == len(correct_set)

        # Checking no 'double' sets in adjustment sets
        assert len(dag.adjustment_sets) == len(set(dag.adjustment_sets))

        # Checking that minimal is the same
        assert dag.adjustment_sets == dag.minimal_adjustment_sets

    def test_mbias(self, arrow_mbias):
        correct_set = [{},
                       {'U1',}, {'U2',},
                       {'U1', 'B'}, {'U1', 'U2'}, {'B', 'U2'},
                       {'U1', 'B', 'U2'}]

        dag = DirectedAcyclicGraph(exposure='X', outcome="Y")
        dag.add_arrows(arrow_mbias)
        dag.calculate_adjustment_sets()

        # Making sure number of adjustment sets are equal to correct sets
        assert len(dag.adjustment_sets) == len(correct_set)

        # Checking no 'double' sets in adjustment sets
        assert len(dag.adjustment_sets) == len(set(dag.adjustment_sets))

        # Checking that all adjustment sets are in the correct
        for i in dag.adjustment_sets:
            if len(i) != 0:
                assert set(i) in list(correct_set)

        assert dag.minimal_adjustment_sets == [()]

    def test_butterfly(self, arrow_butterfly):
        correct_set = [{'U1', 'B'}, {'B', 'U2'}, {'U1', 'B', 'U2'}]

        dag = DirectedAcyclicGraph(exposure='X', outcome="Y")
        dag.add_arrows(arrow_butterfly)
        dag.calculate_adjustment_sets()

        # Making sure number of adjustment sets are equal to correct sets
        assert len(dag.adjustment_sets) == len(correct_set)

        # Checking no 'double' sets in adjustment sets
        assert len(dag.adjustment_sets) == len(set(dag.adjustment_sets))

        # Checking that all adjustment sets are in the correct
        for i in dag.adjustment_sets:
            assert set(i) in list(correct_set)

        for i in dag.minimal_adjustment_sets:
            assert set(i) in [{'U1', 'B'}, {'B', 'U2'}]
