FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod .
COPY . .
RUN go build -o ctf-frontend .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/ctf-frontend .
COPY --from=builder /app/templates ./templates
COPY --from=builder /app/static ./static
EXPOSE 3000
CMD ["./ctf-frontend"]
