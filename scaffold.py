import numpy as np

class BackhaulEstimator:
    # create a prototype that can handle distances in either a 2D grid or a road network
    # concrete implementations of Field need to define a constructor and a _get_dist() function

    _b = 10 # base cost per mile in $/mi

    def __init__(self, field):
        # pass an object of the class FieldPrototype or its child classes
        self.field = field
    
    def _get_radial_area(self, loc, radius):
        '''
        get list of indices that can be used to identify grid locations/nodes and their distance to the loc
        '''

        # get mask
        inner = self.field._cmask(loc, radius)
        outer = self.field._cmask(loc, 2*radius).difference_update(inner)
        outer_dists = {k: self.field._get_dist(loc, k) for k in outer} # dict with outer as index and distance as value
        return inner, outer, outer_dists
    
    def _update_index(self, loc, cost, accepted, d=0):
        '''
        update estimated cost and weight at a specific index based on a resolved request's cost and acceptance status 
        '''
        c_hat = self.field._cost_est[loc]

        # calc alpha coeff to decay effect outside of inner area
        alpha = (d*self._b/cost-1)

        # move estimate toward observed cost if it contains more information
        if accepted or (cost > c_hat):
            movement_factor = alpha*self.field._weights[loc]
            cost_est = (1 - movement_factor)*cost + (movement_factor)*c_hat

        # make current cost estimate stickier
        # TODO: how to update weight properly?
        if accepted:
            weight = self.field._weights[loc]**2
        elif (cost > c_hat):
            weight = self.field._weights[loc]**2 / alpha
        
        self.field._set_loc(loc, cost_est, weight)
    
    def _get_rec_range(self, loc1, loc2):
        '''
        recommend pricing range that trades off between likelihood of acceptance and gathering additional information
        '''
        # TODO
        range = []
        return range

    def get_cost_est(self, loc1, loc2):
        '''
        calculate estimated cost of delivery with cost of getting to loc1, leaving loc2, and travel dist
        '''
        cost_estimate = self.field._cost_est[loc1] + self.field._cost_est[loc2] + self.field._get_dist(loc1, loc2)*self._b
        # calculate price range to offer in order to gain the most information about area. returns length 2 array.
        cost_rec_range = self._get_rec_range(loc1, loc2)
        return cost_estimate, cost_rec_range

    def update_est(self, loc1, loc2, price, accepted):
        '''
        update estimates in areas affected by new offer resolution
        '''
        cost = (price - self._b*self.field._get_dist(loc1, loc2))/2

        # get radial areas around loc1 and loc2 and reconcile the overlap
        radius = cost/self._b
        inner1, outer1, outer_dists1 = self._get_radial_area(loc1, radius)
        inner2, outer2, outer_dists2 = self._get_radial_area(loc2, radius)
        inner = inner1.update(inner2)
        outer = outer1.update(outer2).difference_update(inner)

        # merge outer_dists dictionaries, removing entries in inner and taking minimum dist in case of overlap
        outer_dists = {}
        for k in outer:
            dists = []
            if k in outer_dists1:
                dists.append(outer_dists1[k])
            if k in outer_dists2:
                dists.append(outer_dists2[k])
            outer_dists[k] = min(dists)

        # update cost estimate and weights in affected areas
        for loc in inner:
            self._update_index(loc, cost, accepted)
        for loc in outer:
            self._update_index(loc, cost, accepted, d=outer_dists[loc])
    
    def get_recommended_cost(self, loc1, loc2):
        '''
        convenience function to yield a single price from the estimate and info range
        aiming to maximize the likelihood of a match first, then info gathering
        if est in range, return est
        if est below range, return est
        if est above range, return range high
        '''

        est, range = self.get_cost_est(loc1, loc2)

        if est < range[1]:
            return est
        else:
            return range[1]


class Field2D():
    # create a 2D grid to find weights and distances on

    _cost_est = None
    _weights = None 
    _res = 1

    def __init__(self, xsize, ysize, init_cost=10, res=1):
        '''
        initialize cost estimate grid and weight grid
        '''
        # TODO: tweakable resolution?
        self._cost_est = np.ones([xsize, ysize])*init_cost
        self._weights = np.ones([xsize, ysize])
        self._res = res
    
    def _get_dist(self, loc1, loc2):
        '''
        get distance between two locs
        '''
        return ((loc2[0] - loc1[0])**2 + (loc2[1] - loc1[1]))**(1/2)
    
    def _cmask(self, loc, radius):
        '''
        get all IDs within the given radius (after normalization to indices) of loc
        '''
        radius_normalized = radius/self._res
        a,b = loc
        nx,ny = self._weights.shape
        y,x = np.ogrid[-a:nx-a,-b:ny-b]
        x,y = np.where(x*x + y*y <= radius_normalized*radius_normalized)
        return set([(x[i],y[i]) for i in range(len(x))])
    
    def _set_loc(self, loc, cost_est=None, weight=None):
        '''
        set the cost estimate and weight at a location to new values
        '''
        pass

        if cost_est:
            self._cost_est[loc] = cost_est
        if weight:
            self._weights[loc] = weight
