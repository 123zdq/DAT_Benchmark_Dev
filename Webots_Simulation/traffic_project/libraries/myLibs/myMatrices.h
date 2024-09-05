#pragma once

#include <iostream>
#include <vector>
#include <stdexcept>

#define USING_NAMESPACE_MM using namespace mM;
#define MATRIX myMatrices<real_t>
#define MATRIX_PTR myMatrices<real_t>*

namespace mM {

    template <class T>
    class myMatrices {
    /* 锟斤拷元锟斤拷锟斤拷 */
        // template<class T>
        // friend myMatrices<T> rowCombine(myMatrices<T>& A, myMatrices<T>& B);
        // template<class T, class... Args>
        // friend myMatrices<T> rowCombine(myMatrices<T>& A, myMatrices<T>& B, Args... rest);
        // template<class T>
        // friend myMatrices<T> colCombine(myMatrices<T>& A, myMatrices<T>& B);
        // template<class T, class... Args>
        // friend myMatrices<T> colCombine(myMatrices<T>& A, myMatrices<T>& B, Args... rest);

    private:
        uint16_t rows;
        uint16_t cols;
        T* data;

    public:
        /* 锟斤拷锟叫癸拷锟斤拷 */
        myMatrices(uint16_t rows, uint16_t cols) : rows(rows), cols(cols)
        {
            data = new T[rows * cols];
            clear(0);
        }
        /* 锟斤拷锟斤拷锟斤拷 */
        myMatrices(uint16_t n) : rows(n), cols(n)
        {
            data = new T[rows * cols];
            clear(0);
        }
        ~myMatrices()
        {
            // delete data;
        }

        /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷值统一锟斤拷 */
        void clear(T num)
        {
            if (rows > 0 && cols > 0)
            {
                for (uint16_t i = 0; i < rows; i++)
                {
                    for (uint16_t j = 0; j < cols; j++)
                    {
                        data[i * cols + j] = num;
                    }
                }
            }
        }

        /* 锟斤拷位锟斤拷锟斤拷 */
        void eye()
        {
            if ((rows > 0) && (cols > 0) && (rows == cols))
            {
                for (uint16_t i = 0; i < rows; i++)
                {
                    data[i * cols + i] = 1;
                }
            }
        }
        
        /* 锟斤拷取锟斤拷锟斤拷锟斤拷锟斤拷锟� */
        uint16_t getRows() const {
            return rows;
        }

        /* 锟斤拷取锟斤拷锟斤拷锟斤拷锟斤拷锟� */
        uint16_t getCols() const {
            return cols;
        }
        
        /* 锟斤拷取锟斤拷锟斤拷锟斤拷锟截讹拷位锟矫碉拷元锟斤拷 */
        T getElement(uint16_t row, uint16_t col) const {
            return data[row * cols + col];
        }
        
        /* 锟斤拷锟矫撅拷锟斤拷锟斤拷锟截讹拷位锟矫碉拷元锟斤拷 */
        void setElement(uint16_t row, uint16_t col, T value) {
            data[row * cols + col] = value;
        }

        /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷 */
        void setArray(const T* array, uint16_t length)
        {
            if (rows == length / cols)
            {
                memcpy(data, array, rows * cols * sizeof(T));
            }
            else
            {
            }
        }
        
        /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷 */
        void setRowArray(const T* _array, uint16_t _row)
        {
            if (_row < rows)
            {
                for (int i = 0; i < cols; i++)
                {
                    data[cols * _row + i] = _array[i];//取锟斤拷锟斤拷应锟斤拷锟斤拷锟较碉拷每一锟斤拷元锟斤拷
                }
            }
        }
        
        /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷 */
        void setColArray(const T* _array, uint16_t _col)
        {
            if (_col < cols)
            {
                for (int i = 0; i < rows; i++)
                {
                    data[i * cols + _col] = _array[i];//取锟斤拷锟斤拷应锟斤拷锟斤拷锟较碉拷每一锟斤拷元锟斤拷
                }
            }
        }
        
        /* 锟斤拷锟斤拷默锟斤拷锟斤拷锟斤拷锟斤拷锟酵碉拷锟斤拷锟斤拷锟斤拷锟斤拷 */
        const T* getArray() {
            return data;
        }
        
        /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷 */
        void getRowArray(T* _dst, uint16_t _row)
        {
            if (_row < rows)
            {
                for (int i = 0; i < cols; i++)
                {
                    _dst[i] = data[cols * _row + i];//取锟斤拷锟斤拷应锟斤拷锟斤拷锟较碉拷每一锟斤拷元锟斤拷
                }
            }
        }
        
        /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷 */
        void getColArray(T* _dst, uint16_t _col)
        {
            if (_col < cols)
            {
                for (int i = 0; i < rows; i++)
                {
                    _dst[i] = data[i * cols + _col];//取锟斤拷锟斤拷应锟斤拷锟斤拷锟较碉拷每一锟斤拷元锟斤拷
                }
            }
        }
        
        /* 锟斤拷印锟斤拷锟斤拷 */
        void print() const {
            for (uint16_t i = 0; i < rows; i++) {
                for (uint16_t j = 0; j < cols; j++) {
                    std::cout << getElement(i, j) << " ";
                }
                std::cout << std::endl;
            }
            std::cout << std::endl;
        }

        //锟斤拷锟斤拷臃锟�
        myMatrices<T> operator+(const myMatrices<T>& other) const;
        // 锟斤拷锟斤拷锟斤拷锟�
        myMatrices<T> operator-(const myMatrices<T>& other) const;
        // 锟斤拷锟斤拷朔锟�
        myMatrices<T> operator*(const myMatrices<T>& other) const;
        myMatrices<T> operator*(const T other) const;
        // 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷式
        T determinant() const;
        // 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟绞�
        myMatrices<T> getCofactorMatrix(uint16_t rowToRemove, uint16_t colToRemove) const;
        // 锟斤拷锟斤拷转锟斤拷
        myMatrices<T> transpose() const;
        // 锟斤拷锟斤拷锟斤拷锟斤拷
        myMatrices<T> inverse() const;
        // 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷
        void rowExpansion(myMatrices<T> other);
        // 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷
        void colExpansion(myMatrices<T> other);
    };



    /* 锟斤拷锟斤拷臃锟� */
    template<class T>
    myMatrices<T> myMatrices<T>::operator+(const myMatrices<T>& other) const {

        myMatrices<T> result(rows, cols);

        if (rows != other.rows || cols != other.cols) {
            throw std::invalid_argument("Matrix dimensions are not compatible for addition");
        }
        else
        {
            for (uint16_t i = 0; i < rows; i++) {
                for (uint16_t j = 0; j < cols; j++) {
                    result.setElement(i, j, getElement(i, j) + other.getElement(i, j));
                }
            }
        }

        return result;
    }

    /* 锟斤拷锟斤拷锟斤拷锟� */
    template<class T>
    myMatrices<T> myMatrices<T>::operator-(const myMatrices<T>& other) const {

        myMatrices<T> result(rows, cols);

        if (rows != other.rows || cols != other.cols) {
            throw std::invalid_argument("Matrix dimensions are not compatible for subtraction");
            return result;
        }
        else
        {
            for (uint16_t i = 0; i < rows; i++) {
                for (uint16_t j = 0; j < cols; j++) {
                    result.setElement(i, j, getElement(i, j) - other.getElement(i, j));
                }
            }
        }

        return result;
    }

    /* 锟斤拷锟斤拷朔锟� */
    template<class T>
    myMatrices<T> myMatrices<T>::operator*(const myMatrices<T>& other) const {

        myMatrices<T> result(rows, other.cols);

        if (cols != other.rows) {
            throw std::invalid_argument("Matrix dimensions are not compatible for multiplication");
        }
        else
        {
            for (uint16_t i = 0; i < rows; i++) {
                for (uint16_t j = 0; j < other.cols; j++) {
                    T sum = 0;
                    for (uint16_t k = 0; k < cols; k++) {
                        sum += getElement(i, k) * other.getElement(k, j);
                    }
                    result.setElement(i, j, sum);
                }
            }
        }

        return result;
    }

    /* 锟斤拷锟斤拷锟诫常锟斤拷锟斤拷锟� */
    template<class T>
    myMatrices<T> myMatrices<T>::operator*(const T other) const {
        myMatrices<T> result(rows, cols);
        for (uint16_t i = 0; i < rows; i++)
        {
            for (uint16_t j = 0; j < cols; j++)
            {
                result.setElement(i, j, this->getElement(i, j) * other);
            }
        }
        return result;
    }
 
    /* 锟斤拷锟斤拷转锟斤拷 */
    template<class T>
    myMatrices<T> myMatrices<T>::transpose() const {
        myMatrices<T> result(cols, rows);

        for (uint16_t i = 0; i < rows; i++) {
            for (uint16_t j = 0; j < cols; j++) {
                result.setElement(j, i, getElement(i, j));
            }
        }

        return result;
    }

    /* 锟斤拷锟斤拷锟斤拷锟斤拷 */
    template<class T>
    myMatrices<T> myMatrices<T>::inverse() const {

        myMatrices<T> adj(rows, cols);

        if (rows != cols) {
            throw std::invalid_argument("Matrix is not square");
            return adj;
        }

        T det = determinant();
        if (det == 0) {
            throw std::runtime_error("Matrix is singular; cannot compute inverse");
            return adj;
        }

        for (uint16_t i = 0; i < rows; i++) {
            for (uint16_t j = 0; j < cols; j++) {
                // 锟斤拷锟斤拷(i, j)位锟矫的达拷锟斤拷锟斤拷锟斤拷式
                myMatrices<T> cofactorMatrix = getCofactorMatrix(i, j);
                double cofactor = cofactorMatrix.determinant();

                // 使锟矫帮拷锟斤拷锟斤拷锟斤拷(i, j)位锟矫存储锟斤拷锟斤拷锟斤拷锟斤拷式
                adj.setElement(i, j, cofactor);
            }
        }

        return adj * (1. / det);
    }

    /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷式 */
    template<class T>
    T myMatrices<T>::determinant() const {
        if (rows != cols) {
            throw std::invalid_argument("Matrix must be square to calculate determinant");
            return 0;
        }

        if (rows == 1) {
            return getElement(0, 0);
        }

        if (rows == 2) {
            // 锟斤拷锟斤拷2x2锟斤拷锟斤拷锟斤拷锟斤拷式锟斤拷锟姐公式为 ad - bc
            return getElement(0, 0) * getElement(1, 1) - getElement(0, 1) * getElement(1, 0);
        }

        double det = 0;
        for (uint16_t i = 0; i < cols; i++) {
            // 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟绞斤拷锟街�
            double cofactor = getElement(0, i) * getCofactorMatrix(0, i).determinant();
            // 使锟矫递癸拷锟斤拷锟斤拷锟斤拷锟绞�
            det += (i % 2 == 0 ? 1 : -1) * cofactor;
        }

        return det;
    }

    /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷式 */
    template<class T>
    myMatrices<T> myMatrices<T>::getCofactorMatrix(uint16_t rowToRemove, uint16_t colToRemove) const {

        myMatrices<T> cofactor(rows - 1, cols - 1);

        if (rowToRemove < 0 || rowToRemove >= rows || colToRemove < 0 || colToRemove >= cols) {
            throw std::invalid_argument("Invalid row or column index");
            return cofactor;
        }

        uint16_t cofactorRow = 0;
        for (uint16_t i = 0; i < rows; i++) {
            if (i == rowToRemove) {
                continue; // 锟斤拷锟斤拷要锟狡筹拷锟斤拷锟斤拷
            }

            uint16_t cofactorCol = 0;
            for (uint16_t j = 0; j < cols; j++) {
                if (j == colToRemove) {
                    continue; // 锟斤拷锟斤拷要锟狡筹拷锟斤拷锟斤拷
                }

                cofactor.setElement(cofactorRow, cofactorCol, getElement(i, j));
                cofactorCol++;
            }

            cofactorRow++;
        }

        return cofactor;
    }

    /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷 */
    template<class T>
    void myMatrices<T>::rowExpansion(myMatrices<T> other)
    {
        if (cols != other.cols){
            throw  std::invalid_argument("Matrix dimensions are not compatible for expansion");
        }
        else
        {
            T* p = data;//锟斤拷取原锟斤拷锟节达拷锟街�
            data = new T[(rows + other.rows) * cols];//锟斤拷锟铰凤拷锟斤拷锟节达拷
            memcpy(data, p, sizeof(T)*rows*cols);//锟斤拷原锟斤拷锟斤拷copy
            memcpy(data+(rows * cols), other.getArray(), sizeof(T) * other.rows * other.cols);//copy锟斤拷锟斤拷锟斤拷锟斤拷
            rows = rows + other.rows;//锟斤拷锟斤拷锟斤拷锟斤拷
            delete p;//删锟斤拷原锟斤拷锟斤拷锟节达拷
        }
    }

    /* 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷 */
    template<class T>
    void myMatrices<T>::colExpansion(myMatrices<T> other)
    {
        if (rows != other.rows) {
            throw  std::invalid_argument("Matrix dimensions are not compatible for expansion");
        }
        else
        {
            T* p = data;//锟斤拷取原锟斤拷锟节达拷锟街�
            data = new T[rows * (cols + other.cols)];//锟斤拷锟铰凤拷锟斤拷锟节达拷
            uint16_t n = cols + other.cols;
            for (uint16_t i = 0; i < rows; i++)
            {
                memcpy(data + i*n, p + i*cols, sizeof(T) * cols);//锟斤拷原锟斤拷锟斤拷copy
                memcpy(data + i * n + cols, other.getArray() + i * other.cols, sizeof(T) * other.cols);//copy锟斤拷锟斤拷锟斤拷锟斤拷
            }
            cols = cols + other.cols;//锟斤拷锟斤拷锟斤拷锟斤拷
            delete p;//删锟斤拷原锟斤拷锟斤拷锟节达拷  
        }
    }

    /* 锟斤拷锟斤拷 Kronecker 锟剿伙拷锟斤拷锟轿匡拷matlab锟斤拷kron锟斤拷锟斤拷锟斤拷 */
    template <class T>
    myMatrices<T> kron(myMatrices<T>& A, myMatrices<T>& B) {
        uint16_t m = A.getRows();
        uint16_t n = A.getCols();
        uint16_t p = B.getRows();
        uint16_t q = B.getCols();

        myMatrices<T> result(m * p, n * q);

        for (uint16_t i = 0; i < m; i++) {
            for (uint16_t j = 0; j < n; j++) {
                for (uint16_t k = 0; k < p; k++) {
                    for (uint16_t l = 0; l < q; l++) {
                        result.setElement(i * p + k, j * q + l, A.getElement(i, j) * B.getElement(k, l));
                    }
                }
            }
        }

        return result;
    }

    template <class T, class... Args>
    myMatrices<T> kron(myMatrices<T>& A, myMatrices<T>& B, Args&... rest) {
        uint16_t m = A.getRows();
        uint16_t n = A.getCols();
        uint16_t p = B.getRows();
        uint16_t q = B.getCols();

        myMatrices<T> result(m * p, n * q);

        for (uint16_t i = 0; i < m; i++) {
            for (uint16_t j = 0; j < n; j++) {
                for (uint16_t k = 0; k < p; k++) {
                    for (uint16_t l = 0; l < q; l++) {
                        result.setElement(i * p + k, j * q + l, A.getElement(i, j) * B.getElement(k, l));
                    }
                }
            }
        }

        return kron(result, rest...);
    }

    /* 锟斤拷锟斤拷锟皆角匡拷锟斤拷锟� */
    template <class T>
    myMatrices<T> blkdiag(const myMatrices<T>& A, const myMatrices<T>& B) {

        myMatrices<T> result(A.getRows() + B.getRows(), A.getCols() + B.getCols());

        uint16_t rowOffset = 0;
        uint16_t colOffset = 0;

        for (uint16_t j = 0; j < A.getRows(); j++) {
            for (uint16_t k = 0; k < A.getCols(); k++) {
                result.setElement(rowOffset + j, colOffset + k, A.getElement(j, k));
            }
        }

        rowOffset += A.getRows();
        colOffset += A.getCols();

        for (uint16_t j = 0; j < B.getRows(); j++) {
            for (uint16_t k = 0; k < B.getCols(); k++) {
                result.setElement(rowOffset + j, colOffset + k, B.getElement(j, k));
            }
        }

        rowOffset += B.getRows();
        colOffset += B.getCols();

        return result;
    }

    template <class T, class... Args>
    myMatrices<T> blkdiag(const myMatrices<T>& A, const myMatrices<T>& B, const Args&... rest) {

        myMatrices<T> result(A.getRows() + B.getRows(), A.getCols() + B.getCols());

        uint16_t rowOffset = 0;
        uint16_t colOffset = 0;

        for (uint16_t j = 0; j < A.getRows(); j++) {
            for (uint16_t k = 0; k < A.getCols(); k++) {
                result.setElement(rowOffset + j, colOffset + k, A.getElement(j, k));
            }
        }

        rowOffset += A.getRows();
        colOffset += A.getCols();

        for (uint16_t j = 0; j < B.getRows(); ++j) {
            for (uint16_t k = 0; k < B.getCols(); ++k) {
                result.setElement(rowOffset + j, colOffset + k, B.getElement(j, k));
            }
        }

        rowOffset += B.getRows();
        colOffset += B.getCols();

        return blkdiag(result, rest...);
    }

    /* 锟斤拷锟斤拷锟斤拷锟斤拷锟� */
    template<class T>
    myMatrices<T> zeros(uint16_t n)
    {
        myMatrices<T> result(n, n);
        return result;
    }
    template<class T>
    myMatrices<T> zeros(uint16_t rows, uint16_t cols)
    {
        myMatrices<T> result(rows, cols);
        return result;
    }

    /* 锟斤拷锟斤拷锟斤拷位锟皆斤拷锟斤拷 */
    template<class T>
    myMatrices<T> eye(uint16_t n)
    {
        myMatrices<T> result(n, n);
        for (uint16_t i = 0; i < n; i++)
        {
            result.setElement(i, i, 1);
        }
        return result;
    }

    /* 锟斤拷锟斤拷锟斤拷锟斤拷喜锟斤拷锟斤拷胁锟斤拷锟斤拷斜洌� */
    template<class T>
    myMatrices<T> rowCombine(myMatrices<T>& A,myMatrices<T>& B)
    {
        myMatrices<T> result(A.getRows() + B.getRows(), A.getCols());
        if (A.getCols() != B.getCols()) {
            throw  std::invalid_argument("Matrix dimensions are not compatible for combine");
            return result;
        }
        else
        {
            memcpy(result.data, A.getArray(), sizeof(T) * A.getRows() * A.getCols());//锟斤拷原锟斤拷锟斤拷copy
            memcpy(result.data + (A.getRows() * A.getCols()), B.getArray(), sizeof(T) * B.getRows() * B.getCols());//copy锟斤拷锟斤拷锟斤拷锟斤拷
            return result;
        }
    }

    template <class T, class... Args>
    myMatrices<T> rowCombine(myMatrices<T>& A, myMatrices<T>& B,Args... rest)
    {
        myMatrices<T> result(A.getRows() + B.getRows(), A.getCols());
        if (A.getCols() != B.getCols()) {
            throw  std::invalid_argument("Matrix dimensions are not compatible for combine");
            return result;
        }
        else
        {
            memcpy(result.data, A.getArray(), sizeof(T) * A.getRows() * A.getCols());//锟斤拷原锟斤拷锟斤拷copy
            memcpy(result.data + (A.getRows() * A.getCols()), B.getArray(), sizeof(T) * B.getRows() * B.getCols());//copy锟斤拷锟斤拷锟斤拷锟斤拷
            return rowCombine(result,rest...);
        }
    }

    /* 锟斤拷锟斤拷锟斤拷锟斤拷喜锟斤拷锟斤拷斜锟斤拷胁锟斤拷洌� */
    template<class T>
    myMatrices<T> colCombine(myMatrices<T>& A, myMatrices<T>& B)
    {
        myMatrices<T> result(A.getRows(), A.getCols() + B.getCols());
        if (A.getRows() != B.getRows()) {
            throw  std::invalid_argument("Matrix dimensions are not compatible for combine");
            return result;
        }
        else
        {
            uint16_t n = A.getCols() + B.getCols();
            for (uint16_t i = 0; i < A.getRows(); i++)
            {
                memcpy(result.data + i * n, A.getArray() + i * A.getCols(), sizeof(T) * A.getCols());//锟斤拷原锟斤拷锟斤拷copy
                memcpy(result.data + i * n + A.getCols(), B.getArray() + i * B.getCols(), sizeof(T) * B.getCols());//copy锟斤拷锟斤拷锟斤拷锟斤拷
            }
            return result;
        }
    }

    template<class T, class... Args>
    myMatrices<T> colCombine(myMatrices<T>& A, myMatrices<T>& B, Args... rest)
    {
        myMatrices<T> result(A.getRows(), A.getCols() + B.getCols());
        if (A.getRows() != B.getRows()) {
            throw  std::invalid_argument("Matrix dimensions are not compatible for combine");
            return result;
        }
        else
        {
            uint16_t n = A.getCols() + B.getCols();
            for (uint16_t i = 0; i < A.getRows(); i++)
            {
                memcpy(result.data + i * n, A.getArray() + i * A.getCols(), sizeof(T) * A.getCols());//锟斤拷原锟斤拷锟斤拷copy
                memcpy(result.data + i * n + A.getCols(), B.getArray() + i * B.getCols(), sizeof(T) * B.getCols());//copy锟斤拷锟斤拷锟斤拷锟斤拷
            }
            return colCombine(result,rest...);
        }
    }

}
