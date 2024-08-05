# -*- coding: utf-8 -*-
import pandas as pd

out_file = 'benchmark/literature/badcases2.out'
counterexample_bad_case_file = 'benchmark/literature/badcases2.txt'

df = pd.read_json(out_file, lines=True)

mask = df['states'].apply(lambda x: 'EQU' in x or 'NEQ' in x)
filtered_df = df[mask]

can_verify_per_problem = filtered_df.groupby('file')

mask = df['states'].apply(lambda x: not ('EQU' in x or 'NEQ' in x))
filtered_df = df[mask]

cannot_verify_per_problem = filtered_df.groupby('file')

# counterexamples check failed

ce_df = pd.read_json(counterexample_bad_case_file, lines=True)

counterexample_fail_per_problem = ce_df.groupby('file')

group_sizes_1 = can_verify_per_problem.size().sort_values(ascending=False).to_frame('Supported')
group_sizes_2 = cannot_verify_per_problem.size().sort_values(ascending=False).to_frame('Unsupported')
group_sizes_3 = counterexample_fail_per_problem.size().sort_values(ascending=False).to_frame('CounterexampleFailures')

# group_sizes = pd.merge(group_sizes_1.reset_index(), group_sizes_2.reset_index(), how='inner', on=['file'])
#
# group_sizes = pd.merge(group_sizes.reset_index(), group_sizes_3.reset_index(), how='inner', on=['file']).sort_values(
#     by=['Unsupported', 'Supported'],
#     ascending = [False, True])

support_unsupport = pd.merge(group_sizes_1, group_sizes_2, how='outer', on='file')
merged = pd \
    .merge(support_unsupport, group_sizes_3, how='outer', on='file') \
    .sort_values(by=['Unsupported', 'Supported'], ascending=[False, True])

print(merged.to_string())
# print(group_sizes_3.to_string())

# for file, size in group_sizes_2.items():
#     print(f"File: {file}, Size: {size}")

support_unsupport = pd.merge(group_sizes_1, group_sizes_2, how='outer', on='file')
merged = pd \
    .merge(support_unsupport, group_sizes_3, how='outer', on='file') \
    .sort_values(by=['CounterexampleFailures', 'Unsupported', 'Supported'], ascending=[False, False, True])

print(merged.to_string())
