import pandas as pd


def generate_coverage_rq1(tool, workload, filename):
    df = pd.read_csv(filename)
    if workload != 'Literature':
        return print(f"{tool},{workload},{df['unsupported'].sum() + df['checked'].sum() + df['disproved'].sum()},0,0")
    else:
        literature_has_ic = [
            'literature_cos/fkPennTR',
            'literature_cos/ex2sigmod83',
            'literature_cos/ex1sigmod92',
            'literature_cos/ex2sigmod92',
            'literature_cos/ex2sigmod92simpl',
            'literature_cos/ex3sigmod92'
        ]
        print(
            f"{tool},{workload},{df.loc[(df['unsupported'] == 1) | df['problem_id'].isin(literature_has_ic)].shape[0]},"
            f"{df.loc[~df['problem_id'].isin(literature_has_ic), 'checked'].sum()},"
            f"{df.loc[~df['problem_id'].isin(literature_has_ic), 'disproved'].sum()}")


def generate_coverage_rq2(tool, workload, filename):
    df = pd.read_csv(filename)
    print(f"{tool},{workload},{df['unsupported'].sum()},{df['checked'].sum()},{df['disproved'].sum()}")


if __name__ == '__main__':
    # RQ1
    print("=======RQ1 (coverage.csv)=======")
    generate_coverage_rq1('Cosette', 'LeetCode', 'raw_results/cosette_leetcode.csv')
    generate_coverage_rq1('Cosette', 'Calcite', 'raw_results/cosette_calcite.csv')
    generate_coverage_rq1('Cosette', 'Literature', 'raw_results/cosette_literature.csv')
    generate_coverage_rq1('Qex', 'LeetCode', 'raw_results/qex_leetcode.csv')
    generate_coverage_rq1('Qex', 'Calcite', 'raw_results/qex_calcite.csv')
    generate_coverage_rq1('Qex', 'Literature', 'raw_results/qex_literature.csv')
    generate_coverage_rq1('HoTTSQL', 'LeetCode', 'raw_results/hott_leetcode.csv')
    generate_coverage_rq1('HoTTSQL', 'Calcite', 'raw_results/hott_calcite.csv')
    generate_coverage_rq1('HoTTSQL', 'Literature', 'raw_results/hott_literature.csv')

    # RQ2
    print("=======RQ2 (coverage_no_IC.csv)=======")
    generate_coverage_rq2('Cosette', 'LeetCode', 'raw_results/cosette_leetcode.csv')
    generate_coverage_rq2('Cosette', 'Calcite', 'raw_results/cosette_calcite.csv')
    generate_coverage_rq2('Cosette', 'Literature', 'raw_results/cosette_literature.csv')
    generate_coverage_rq2('Qex', 'LeetCode', 'raw_results/qex_leetcode.csv')
    generate_coverage_rq2('Qex', 'Calcite', 'raw_results/qex_calcite.csv')
    generate_coverage_rq2('Qex', 'Literature', 'raw_results/qex_literature.csv')
    generate_coverage_rq2('HoTTSQL', 'LeetCode', 'raw_results/hott_leetcode.csv')
    generate_coverage_rq2('HoTTSQL', 'Calcite', 'raw_results/hott_calcite.csv')
    generate_coverage_rq2('HoTTSQL', 'Literature', 'raw_results/hott_literature.csv')
