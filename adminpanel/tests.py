import pandas as pd
from cluster_analysis import ClusterAnalysis, mark_of_question


class TestClusterAnalysis:
    def test_preprocessing(self):
        arr = []
        with open("test_db.csv", "r", encoding="utf-8") as f:
            s = f.readline()
            while s:
                x = int(s.split(" --- ")[2])
                if x == 0:
                    x = mark_of_question.have_not_answer
                elif x == 1:
                    x = mark_of_question.have_low_score
                elif x == 2:
                    x = mark_of_question.have_high_score
                else:
                    x = mark_of_question.have_not_score
                arr.append(
                    {"text": s.split(" --- ")[0], "date": s.split(" --- ")[1], "type": x}
                )
                s = f.readline()
        CA = ClusterAnalysis()
        data = CA.get_clusters_keywords(arr)
        assert len(data) == 3
        assert data[1] == 150
        assert data[2] == 49
        data = data[0]
        with open('test_true_result.csv', 'r', encoding='utf-8') as f:
            for cluster in range(len(data)):
                for i in range(len(data[cluster][0])):
                    assert data[cluster][0][i][0] == f.readline()[:-1]
                    assert data[cluster][0][i][1].name == f.readline()[:-1]
                for i in range(len(data[cluster][1])):
                    assert data[cluster][1][i] == f.readline()[:-1]
                for i in range(len(data[cluster][2])):
                    assert data[cluster][2][i] == f.readline()[:-1]

