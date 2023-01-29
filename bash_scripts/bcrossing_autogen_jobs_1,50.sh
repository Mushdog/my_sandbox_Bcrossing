python sandbox.py --grouping sample --sample_sizes 1 --num_samples 50 --dataset bcrossing --compute_standards --indices 1,50 
python sandbox.py --grouping sample --sample_sizes 6 --num_samples 50 --dataset bcrossing  --compute_standards --indices 1,50 
python sandbox.py --grouping sample --sample_sizes 12 --num_samples 50 --dataset bcrossing  --compute_standards --indices 1,50

python sandbox.py --grouping sample --sample_sizes 61 --num_samples 50 --dataset bcrossing --indices 1,50

python sandbox.py --grouping sample --sample_sizes 122 --num_samples 50 --dataset bcrossing --indices 1,50
python sandbox.py --grouping sample --sample_sizes 614 --num_samples 50 --dataset bcrossing  --indices 1,50
python sandbox.py --grouping sample --sample_sizes 1229 --num_samples 50 --dataset bcrossing --indices 1,50 
python sandbox.py --grouping sample --sample_sizes 2458 --num_samples 50 --dataset bcrossing --indices 1,50 
python sandbox.py --grouping sample --sample_sizes 3687 --num_samples 50 --dataset bcrossing --indices 1,50
python sandbox.py --grouping sample --sample_sizes 4917 --num_samples 50 --dataset bcrossing --indices 1,50
python sandbox.py --grouping sample --sample_sizes 6146 --num_samples 50 --dataset bcrossing --indices 1,50
python sandbox.py --grouping sample --sample_sizes 7375 --num_samples 50 --dataset bcrossing --indices 1,50
python sandbox.py --grouping sample --sample_sizes 8605 --num_samples 50 --dataset bcrossing --indices 1,50
python sandbox.py --grouping sample --sample_sizes 9834 --num_samples 50 --dataset bcrossing --indices 1,50
python sandbox.py --grouping sample --sample_sizes 11063 --num_samples 50 --dataset bcrossing --indices 1,50
python sandbox.py --grouping sample --sample_sizes 12170 --num_samples 50 --dataset bcrossing --indices 1,50

python sandbox.py --compute_standards --dataset bcrossing --indices 1,50

--send_to_out 

'''
[    1.     6.    12.    61.   122.   614.  1229.  2458.  3687.  4917.
  6146.  7375.  8605.  9834. 11063. 12170. 12280.]
12293
'''
'''
tiny_data.sh:

python sandbox.py --grouping sample --sample_sizes 12280 --num_samples 50 --dataset bcrossing --indices 1,50

python sandbox.py --grouping sample --sample_sizes 12290 --num_samples 50 --dataset bcrossing --indices 1,50

python process_all.py
'''

python sandbox.py --grouping age --userfrac 0.5 --ratingfrac 1.0 --dataset bcrossing --num_samples 50 --indices 1,50 

python sandbox.py --grouping state --userfrac 0.5 --ratingfrac 1.0 --dataset bcrossing --num_samples 50 --indices 1,50 
