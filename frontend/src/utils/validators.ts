/**
 * 校验手机号格式
 */
export function isValidPhone(phone: string): boolean {
  return /^1[3-9]\d{9}$/.test(phone)
}

/**
 * 校验密码复杂度（8-20 位，至少包含字母和数字）
 */
export function isValidPassword(password: string): boolean {
  return /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,20}$/.test(password)
}

/**
 * 校验 6 位验证码
 */
export function isValidCode(code: string): boolean {
  return /^\d{6}$/.test(code)
}
