package com.ai.companion.exception;

import com.ai.companion.common.Result;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(RuntimeException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public Result<?> handleRuntimeException(RuntimeException e) {
        return Result.error(500, e.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<?> handleValidationException(MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldError() != null
                ? e.getBindingResult().getFieldError().getDefaultMessage()
                : "参数验证失败";
        return Result.error(400, message);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Result<?> handleIllegalArgumentException(IllegalArgumentException e) {
        return Result.error(400, e.getMessage());
    }

    /** 邮件未成功发送：503，前端展示业务提示，不能伪装成验证码发送成功。 */
    @ExceptionHandler(EmailSendException.class)
    @ResponseStatus(HttpStatus.SERVICE_UNAVAILABLE)
    public Result<?> handleEmailSendException(EmailSendException e) {
        return Result.error(503, e.getMessage());
    }

    /** 下游服务（如 8002 RAG）不可用：502，与自身 500 区分开，前端提示语更准确。 */
    @ExceptionHandler(ServiceUnavailableException.class)
    @ResponseStatus(HttpStatus.BAD_GATEWAY)
    public Result<?> handleServiceUnavailableException(ServiceUnavailableException e) {
        return Result.error(502, e.getMessage());
    }
}
