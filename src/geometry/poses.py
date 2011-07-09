from . import (angle_from_rot2d, rotz, axis_angle_from_rotation, hat_map_2d,
    zeros, contract, assert_allclose, check, np, rot2d, new_contract, logm, expm)


def check_SE(M):
    ''' Checks that the argument is in the special euclidean group. '''
    R, t, zero, one = extract_pieces(M) #@UnusedVariable
    check('SO', R)
    assert_allclose(one, 1, err_msg='I expect the lower-right to be 1')
    assert_allclose(zero, 0, err_msg='I expect the bottom component to be 0.')

def check_se(M):
    ''' Checks that the input is in the special euclidean Lie algebra. '''
    omega, v, Z, zero = extract_pieces(M) #@UnusedVariable
    check('so', omega)
    assert_allclose(Z, 0, err_msg='I expect the lower-right to be 0.')
    assert_allclose(zero, 0, err_msg='I expect the bottom component to be 0.')


new_contract('se', check_se)
new_contract('SE', check_SE)
new_contract('SE2', 'array[3x3], SE')
new_contract('se2', 'array[3x3], se')
new_contract('SE3', 'array[4x4], SE')
new_contract('se3', 'array[4x4], se')
    
    
@contract(x='array[NxN]', returns='tuple(array[MxM],array[M],array[M],number),M=N-1')
def extract_pieces(x):
#    print x.__class__
#    x = np.array(x) # otherwise it could get fooled by <class 'numpy.matrixlib.defmatrix.matrix'>
    # the shape would be (2,1) instead of (2,)
    # TODO: change logm
    M = x.shape[0] - 1
    a = x[0:M, 0:M]
    b = x[0:M, M]
    c = x[M, 0:M]
    d = x[M, M]
    return a, b, c, d

@contract(a='array[MxM]', b='array[M]', c='array[M]', d='number', returns='array[NxN],N=M+1') 
def combine_pieces(a, b, c, d):
    M = a.shape[0]
    x = zeros((M + 1, M + 1)) 
    x[0:M, 0:M] = a
    x[0:M, M] = b
    x[M, 0:M] = c
    x[M, M] = d
    return x

# TODO: specialize for SE2, SE3

@contract(returns='SE2')
def SE2_identity():
    return np.eye(3)

@contract(returns='SE3')
def SE3_identity():
    return np.eye(4)

@contract(R='array[NxN],SO', t='array[N]', returns='array[MxM],M=N+1,SE') 
def pose_from_rotation_translation(R, t):
    return combine_pieces(R, t, t * 0, 1)

# TODO: make specialized    
SE2_from_rotation_translation = pose_from_rotation_translation
SE3_from_rotation_translation = pose_from_rotation_translation


@contract(pose='array[NxN],SE', returns='tuple(array[MxM], array[M]),M=N-1')
def rotation_translation_from_pose(pose):
    R, t, zero, one = extract_pieces(pose) #@UnusedVariable
    return R, t

# TODO: make more efficient
rotation_translation_from_SE2 = rotation_translation_from_pose
rotation_translation_from_SE3 = rotation_translation_from_pose

@contract(pose='SE2')
def translation_from_SE2(pose):
    # TODO: make it more efficient
    R, t, zero, one = extract_pieces(pose) #@UnusedVariable
    return t

@contract(pose='SE3')
def translation_from_SE3(pose):
    # TODO: make it more efficient
    R, t, zero, one = extract_pieces(pose) #@UnusedVariable
    return t

    
@contract(t='array[2]|seq[2](number)', theta='number', returns='SE2')
def SE2_from_translation_angle(t, theta):
    ''' Returns an element of SE2 from translation and rotation. '''
    t = np.array(t)
    return combine_pieces(rot2d(theta), t, t * 0, 1)

@contract(pose='SE2', returns='tuple(array[2],float)')
def translation_angle_from_SE2(pose):
    R, t, zero, one = extract_pieces(pose) #@UnusedVariable
    return t, angle_from_rot2d(R)

# TODO: write tests for this, and other function
@contract(xytheta='array[3]|seq[3](number)', returns='SE2')
def SE2_from_xytheta(xytheta):
    ''' Returns an element of SE2 from translation and rotation. '''
    return SE2_from_translation_angle([xytheta[0], xytheta[1]], xytheta[2])


 
@contract(linear='array[2]|seq[2](number)', angular='number', returns='se2')
def se2_from_linear_angular(linear, angular):
    ''' Returns an element of se2 from linear and angular velocity. ''' 
    linear = np.array(linear)
    M = hat_map_2d(angular) 
    return combine_pieces(M, linear, linear * 0, 0)

@contract(vel='se2', returns='tuple(array[2],float)')
def linear_angular_from_se2(vel):
    M, v, Z, zero = extract_pieces(vel) #@UnusedVariable
    omega = M[1, 0]
    return v, omega

# TODO: add to docs
@contract(pose='SE2', returns='se2')
def se2_from_SE2_slow(pose):
    ''' Converts a pose to its Lie algebra representation. '''
    R, t, zero, one = extract_pieces(pose) #@UnusedVariable
    # FIXME: this still doesn't work well for singularity
    W = np.array(logm(pose).real)
    M, v, Z, zero = extract_pieces(W) #@UnusedVariable
    M = 0.5 * (M - M.T)
    if np.abs(R[0, 0] - (-1)) < 1e-10:
        # cannot use logarithm for log(-I), it gives imaginary solution
        M = hat_map_2d(np.pi) 
    
    return combine_pieces(M, v, v * 0, 0)    

@contract(pose='SE2', returns='se2')
def se2_from_SE2(pose):
    '''
        Converts a pose to its Lie algebra representation.
        
        See Bullo, Murray "PD control on the euclidean group" for proofs.
    '''
    R, t, zero, one = extract_pieces(pose) #@UnusedVariable
    w = angle_from_rot2d(R)
    
    w_abs = np.abs(w)
    # FIXME: singularity
    if w_abs < 1e-8:
        a = 1
    else:
        a = (w_abs / 2) / np.tan(w_abs / 2)
    A = np.array([[a, w / 2], [-w / 2, a]])

    v = np.dot(A, t)
    w_hat = hat_map_2d(w)
    return combine_pieces(w_hat, v, v * 0, 0)    


@contract(returns='SE2', vel='se2')
def SE2_from_se2(vel):
    ''' Converts from Lie algebra representation to pose. 
            
        See Bullo, Murray "PD control on the euclidean group" for proofs.
    '''
    w = vel[1, 0]
    R = rot2d(w)
    v = vel[0:2, 2]
    if np.abs(w) < 1e-8:
        R = np.eye(2)
        t = v
    else:
        A = np.array([
            [ np.sin(w) , np.cos(w) - 1],
            [1 - np.cos(w) , np.sin(w)]        
        ]) / w
        t = np.dot(A, v) 
    return combine_pieces(R, t, t * 0, 1)

@contract(returns='SE2', vel='se2')
def SE2_from_se2_slow(vel):
    X = expm(vel)
    X[2, :] = [0, 0, 1]
    return X

@contract(pose='SE2', returns='SE3')
def SE3_from_SE2(pose):
    ''' Embeds a pose in SE2 to SE3, setting z=0 and upright. '''
    t, angle = translation_angle_from_SE2(pose)
    return pose_from_rotation_translation(rotz(angle), np.array([t[0], t[1], 0]))
        
@contract(pose='SE3', returns='SE2')
def SE2_from_SE3(pose, check_exact=True):
    ''' 
        Projects a pose in SE3 to SE2.
    
        If check_exact is True, it will check that z = 0 and axis = [0,0,1].
    '''
    rotation, translation = rotation_translation_from_pose(pose)
    axis, angle = axis_angle_from_rotation(rotation)
    if check_exact:
        err_msg = 'I expect that z=0 when projecting to SE2 (check_exact=True).'
        assert_allclose(translation[2], 0, err_msg=err_msg)
        # normalize angle z
        axis *= np.sign(axis[2])
        err_msg = ('I expect that the rotation is around [0,0,1] '
                  'when projecting to SE2 (check_exact=True).')
        assert_allclose(axis, [0, 0, 1], err_msg=err_msg)
    
    return SE2_from_translation_angle(translation[0:2], angle)
    
    
    


