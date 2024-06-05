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
                    {
                        "text": s.split(" --- ")[0],
                        "date": s.split(" --- ")[1],
                        "type": x,
                    }
                )
                s = f.readline()
        CA = ClusterAnalysis()
        data = CA.get_clusters_keywords(arr)
        with open("test_true_result.csv", "r", encoding="utf-8") as f:
            assert data[2] == int(f.readline()[:-1])
            assert data[1] == int(f.readline()[:-1])
            assert "" == f.readline()[:-1]
            for ar in data[0]:
                assert len(ar[0]) == int(f.readline()[:-1])
                for a in ar[1]:
                    assert a == f.readline()[:-1]
                assert ar[2][0] == f.readline()[:-1]
                assert ar[2][1] == f.readline()[:-1]
                assert "" == f.readline()[:-1]
