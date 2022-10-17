import math
def anglePM180(degrees):
    
     # Stolen from Bob S.
     #
     # This converts an angle (in degrees) into the range &gt;=-180 to &lt;180
     # (180 becomes -180).
     # @param degrees an angle (in degrees)
     # @return the angle (in degrees) in the range &gt;=-180 to &lt;180.
     # not finite it returns 0.
     
    if not math.isfinite(degrees):
        return 0

    while degrees < -180: 
        degrees += 360
    while degrees >= 180:
         degrees -= 360

    return degrees;

     ##
     # This converts an angle (in degrees) into the range >=0 to <360.
     #
def angle0360(degrees):
        if not math.isfinite(degrees):
            return 0;

        while degrees < 0:
            degrees += 360.
        while degrees >= 360.:
            degrees -= 360.

        return degrees

#
# Takes in the x range as east most, west most and constrains accordingly returning a subset as a DataFrame
#
def getLonConstraint(xloDbl, xhiDbl, hasLon360, is180, lonname, in_df):
    out_df = in_df
    if (xloDbl < xhiDbl and abs(xhiDbl - xloDbl) < 355.0) or ((xloDbl > xhiDbl) and abs(xhiDbl - xloDbl) > 5.0 ):
        if is180:
            if xloDbl < xhiDbl:
                # Going west to east does not cross dateline, normal constraint
                print('east west normal')
                if ( (xloDbl <= 180 and xloDbl >= -180.) and (xhiDbl <= 180 and xhiDbl >= -180.) ) or ( (xloDbl >= 180.0 and xhiDbl >= 180.) and not hasLon360 ):
                    print('straight')
                    out_df = in_df.loc[(in_df[lonname]>=anglePM180(xloDbl)) & (in_df[lonname]<=anglePM180(xhiDbl))]
                # Crosses 180 two parts since we don't have lon360
                elif xloDbl <= 180.0 and xhiDbl >= 180.0 and not hasLon360:
                    print('east west crosses')
                    out_df = in_df.loc[(in_df[lonname]>=anglePM180(xloDbl)) & (in_df.loc[in_df[lonname]<=180])]
                    out_df = out_df.loc[(out_df[lonname]>=-180) & (out_df.loc[in_df[lonname]<=anglePM180(xhiDbl)])]
                    # Going east to west does not cross Greenwich, normal lon360 constraint from lon360 input
                    # lon360 boolean indicates data set has has such a variable. If not, don't constrain on lon where lon360 is needed
                elif xloDbl <= 360. and xloDbl >= 0. and xhiDbl <= 360. and xhiDbl >= 0.0 and hasLon360:
                    print('skipping long')
                    out_df = in_df.loc[(in_df['lon360']>=xloDbl) & (in_df['lon360']<=xhiDbl)]
            elif xloDbl > xhiDbl:
                # Going west to east
                # lon360 boolean varifies data has has such a varaible. If not, don't constrain on lon where lon360 is needed
                if xloDbl <= 180.0 and xloDbl >= -180.0 and xhiDbl <= 180.0 and xhiDbl >= -180.0:
                    print('west to east')
                    # Going west to east over dateline, but not greenwich, convert to lon360 from -180 to 180 input
                    if xloDbl > 0 and xhiDbl < 0 and hasLon360:
                        print('has 360')
                        xhiDbl = xhiDbl + 360;
                        out_df = in_df.loc[df['lon360']>=xloDbl]
                        out_df = out_df.loc[out_df['lon360']<=xhiDbl]
                    else:
                        print('does not cross')
                        out_df = in_df.loc[(in_df[lonname]>=xloDbl) & (in_df[lonname]<180)]
                        out_df = out_df.loc[(out_df[lonname]>=-180) & out_df[lonname]<=xhiDbl]
                elif xloDbl <= 360.0 and xloDbl >= 0. and xhiDbl <= 360.0 and xhiDbl >= 0.0:
                    # Going west to east does not cross dateline, from 360 input, just normal -180 to 180
                    if xloDbl > 180.0 and xhiDbl < 180.0:
                        print('west east no dateline')
                        xloDbl = anglePM180(xloDbl);
                        xhiDbl = anglePM180(xhiDbl);
                        out_df = in_df.loc[(in_df[lonname]>=xloDbl) & (in_df[lonname]<=xhiDbl)]
                    elif xloDbl > 180.0 and xhiDbl > 180.0:
                        print('west east last block')
                        out_df = in_df.loc[(in_df[lonname]>=anglePM180(xloDbl)) & (in_df[lonname]<=180)]
                        out_df = out_df.loc[(out_df[lonname]>=-180) & (out_df[lonname]<=anglePM180(xhiDbl))]
        else:
            print('data on 0 360')
            if xloDbl < xhiDbl:
                # Going west to east does not cross 180, normal constraint
                # Going east to west does not cross Greenwich, normal lon360
                # with values normalized to 0 360 since that's what the data are
                if (xloDbl <= 0.0 and xloDbl >= -180.0 and xhiDbl <= 0.0 and xhiDbl >= -180.0) or \
                        (xloDbl <= 180.0 and xloDbl >= 0.0 and xhiDbl <= 180.0 and xhiDbl >= 0.0) or \
                        (xloDbl <= 360.0 and xloDbl >= 0.0 and xhiDbl <= 360.0 and xhiDbl >= 0.0):
                    out_df = in_df.loc[(in_df[lonname]>=angle0360(xloDbl)) & (in_df[lonname]<=angle0360(xhiDbl))]
                elif  xhiDbl > 0.0:
                    out_df = in_df.loc[(in_df[lonname]>=angle0360(xloDbl)) & (df[lonname]<360.0)]
                    out_df = out_df.loc[(out_df[lonname]>=0.0) & (out_df[lonname]<=angle0360(xhiDbl))]         
            elif xloDbl > xhiDbl:
                # Going west to east
                # lon360 boolean data has has such a varaible. If not, don't constrain on lon where lon360 is needed
                if xloDbl <= 180.0 and xloDbl >= -180.0 and xhiDbl <= 180.0 and xhiDbl >= -180.0:
                    # Going west to east over dateline, but not greenwich, convert to lon360 from -180 to 180 input
                    if xloDbl > 0.0 and xhiDbl < 0.0:
                        out_df = in_df.loc[(in_df[lonname]>=angle0360(xloDbl)) & (in_df[lonname]<=angle0360(xhiDbl))]
                    elif xloDbl <= 0.0 and xhiDbl <= 0.0:
                        out_df = in_df.loc[(in_df[lonname]>=angle0360(xloDbl)) & (in_df[lonname]<360)]
                        out_df = out_df.loc[(out_df[lonname]>=0) & (out_df[lonname]<=angle0360(xhiDbl))]
                elif xloDbl <= 360.0 and xloDbl >= 0.0 and xhiDbl <= 360.0 and xhiDbl >= 0.0:
                    # Going west to east from 360 input and 360 data get in two chunks
                    out_df = in_df.loc[(in_df[lonname]>=angle0360(xloDbl)) & (in_df[lonname]<=360.0)]
                    out_df = out_df.loc[(out_df[lonname]>=0.0) & (out_df[lonname]<=angle0360(xhiDbl))]
    return out_df     
