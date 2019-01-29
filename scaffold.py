import numpy as np

class BackhaulEstimator:
    # create a prototype that can handle distances in either a 2D grid or a road network
    # concrete implementations of Field need to define a constructor and a _get_dist() function

    _cost_est = []
    _weights = []
    _last_dir = [] # TODO: implement suspected direction of true value (maybe roll into weight?)
    _b = 10 # base cost per mile in $/mi

    def __init__(field):
        # pass an object of the class FieldPrototype or its child classes
        self.field = field
    
    # redefine in child class
    def _get_dist(self, loc1, loc2):
        # get distance between two locs in miles
        return None

    # redefine in child class
    def _get_radial_area(self, loc, radius):
        # get list of indices that can be used to identify grid locations/nodes and their distance to the loc
        inner = set()
        # inner_dists = Set() # no need to keep distances of inner, since they're updated blanket
        outer = set() # exclude indices in inner
        outer_dists = None # dict with outer as index and distance as value
        return inner, outer, outer_dists

    def _get_areas(self, loc1, loc2, radius):
        # get radial areas between loc1 and loc2 and reconcile the overlap
        inner1, outer1, outer_dists1 = self._get_radial_area(loc1, radius)
        inner2, outer2, outer_dists2 = self._get_radial_area(loc2, radius)
        inner = inner1.add(inner2) # TODO: fix syntax
        outer = outer1.add(outer2).remove(inner)
        # merge outer_dists dictionaries, taking minimum dist in case of overlap
        # remove entries in inner
        outer_dists = outer_dists1.add(outer_dists2)
        return inner, outer, outer_dists

    def _update_cost(self, cost, accepted, d, c_hat, weight, alpha):
        # find the cost
        # TODO: translate accepted to 1 or 0
        # TODO: figure this out
        return (1 - accepted*weight)*cost + (accepted*weight)*c_hat
    
    def _update_index(self, loc, cost, accepted, d=0):
        # update estimated cost and weight at index based on a resolved request's cost and acceptance status 
        c_hat = self._cost_est[loc]

        # calc alpha coeff
        alpha = (d*self._b/cost-1)

        # beta = 1 # in every situation where update happens beta = 1
        if accepted or (cost > c_hat):
            self._cost_est[loc] = self._update_cost(cost, accepted, d, c_hat, self._weights[loc], alpha)

        if accepted:
            self._weights[loc] = self._weights[loc]**2
        elif (cost > c_hat):
            self._weights[loc] = self._weights[loc]**2 / alpha
    
    def _get_rec_range(self, loc1, loc2):
        # TODO
        range = []
        return range

    def get_cost_est(self, loc1, loc2):
        # calculate estimated cost of delivery with cost of getting to loc1, leaving loc2, and travel dist
        cost_estimate = self._cost_est[loc1] + self._cost_est[loc2] + self._get_dist(loc1, loc2)*self._b
        # calculate price range to offer in order to gain the most information about area. returns length 2 array.
        cost_rec_range = self._get_rec_range(loc1, loc2)
        return cost_estimate, cost_rec_range

    def update_radius_areas(self, loc1, loc2, price, accepted):
        # get areas to be affected by new offer resolution and update accordingly
        cost = (price - self._b*self._get_dist(loc1, loc2))/2
        inner, outer, outer_dists = self._get_areas(loc1, loc2, cost/self._b)

        for loc in inner:
            self._update_index(loc, cost, accepted)
        for loc in outer:
            self._update_index(loc, cost, accepted, d=outer_dists[loc])
    
    def get_recommended_cost(self, loc1, loc2):
        # convenience function to yield a single price from the estimate and info range
        # aiming to maximize the likelihood of a match first, then info gathering
        # if est in range, return est
        # if est below range, return est
        # if est above range, return range high

        est, range = self.get_cost_est(loc1, loc2)

        if est < range[1]:
            return est
        else:
            return range[1]


class(FieldProtoype):
    # 

class Field2D(FieldPrototype):
    # create a 2D grid to find weights and distances on

    def __init__(self, xsize, ysize, init_cost=10):
        # initialize cost estimate grid and weight grid
        # TODO: tweakable resolution?
        self._cost_est = np.ones([xsize, ysize])*init_cost
        self._weights = np.ones([xsize, ysize])
    
    def update_radius_areas(self, loc, radius, price, accepted):
        pass
    


        
